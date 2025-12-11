from typing import Callable
import threading
import json
import atexit
from managers import redis_manager, task_manager, user_manager
from utility import logger
from schema.messaging import (
    AvailabilityResultMessage,
    QueueAllAvailabilityChecksCommand
)


def _handle_availability_request(payload: dict):
    # Add validation to ensure the payload has the required keys.
    required_keys = ["username", "store", "card_data"]
    if not all(key in payload for key in required_keys):
        logger.error(
            f"Invalid 'availability_request' payload. Missing required keys."
            f" Payload: {payload}"
        )
        return

    # If validation passes, proceed to queue the task.
    task_manager.queue_task(
        task_manager.task_definitions.UPDATE_AVAILABILITY_SINGLE_CARD,
        payload["username"],
        payload["store"],
        payload["card_data"],
    )


def _handle_queue_all_availability_checks(payload: dict):
    username = payload.get("username")
    if not username:
        logger.error(
            f"Invalid 'queue_all_availability_checks' payload. Missing "
            f"'username'. Payload: {payload}"
        )
        return

    stores = user_manager.get_selected_stores(username)
    user_cards = user_manager.load_card_list(username)

    for store in stores:
        for card in user_cards:
            # Pass the full card data model, not just the name.
            task_manager.queue_task(
                task_manager.task_definitions.UPDATE_AVAILABILITY_SINGLE_CARD,
                username,
                store.slug,
                card.model_dump(),
            )


HANDLER_MAP: dict[str, Callable] = {
    AvailabilityResultMessage.name:
    _handle_availability_request,
    QueueAllAvailabilityChecksCommand.name:
    _handle_queue_all_availability_checks,
}


class _Scheduler_Listener:
    """
    Manages a background thread to listen for results from
    workers on a Redis Pub/Sub channel.
    This is implemented as a singleton to ensure only one
    listener thread is active.
    """

    def __init__(self):
        self.thread = None
        self.pubsub = None

    def start(self):
        """Starts the listener thread if it's not already running."""
        if self.thread and self.thread.is_alive():
            logger.warning("Scheduler listener thread is already running.")
            return

        self.thread = threading.Thread(target=self._listen, daemon=True)
        self.thread.start()
        # Register the stop method to be called on application exit.
        atexit.register(self.stop)

    def stop(self):
        """Signals the listener thread to stop and cleans up resources."""
        logger.info("🛑 Shutting down worker results listener...")
        if self.pubsub:
            # This will cause the loop in _listen() to exit.
            self.pubsub.close()
        if self.thread:
            # Wait for the thread to finish cleanly.
            self.thread.join(timeout=5)
        logger.info("✅ Scheduler results listener shut down gracefully.")

    def _listen(self):
        """The actual listener function that runs in the background thread."""
        self.pubsub = redis_manager.pubsub(ignore_subscribe_messages=True)
        self.pubsub.subscribe("scheduler-requests")
        logger.info(
            "🎧 Scheduler results listener started. Subscribed to "
            "'scheduler-requests' channel."
        )

        try:
            for message in self.pubsub.listen():
                try:
                    data = json.loads(message["data"])
                    command_type = data.get("type")
                    handler = HANDLER_MAP.get(command_type)
                    if handler:
                        payload = data.get("payload", {})
                        handler(payload)
                    else:
                        raise ValueError(f"No handler found for command type "
                                         f"'{command_type}' on "
                                         "'scheduler-requests' channel.")
                except Exception as e:
                    logger.error(
                        f"Failed to process scheduler-requests message: {e}."
                        f" Message: {message.get('data')}"
                    )
                    try:
                        # Move the failed message to a dead-letter queue
                        redis_manager.get_redis_connection().rpush(
                            "scheduler-requests-dlq", message.get("data")
                        )
                    except Exception as dlq_e:
                        logger.error(f"Failed to push message to DLQ: {dlq_e}")

        except Exception as e:
            # This block will be reached when self.pubsub.close() is called,
            # or if there's a connection error.
            logger.info(f"Scheduler listener loop exiting: {e}")


# Create a single instance of the listener.
_listener_instance = _Scheduler_Listener()


def start_scheduler_listener(app):
    """Public function to start the singleton worker listener."""
    _listener_instance.start()
