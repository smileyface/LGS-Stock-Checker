import threading
import json
import atexit
from managers import redis_manager, task_manager, user_manager
from utility import logger

def _handle_availability_request(payload: dict):
    # Add validation to ensure the payload has the required keys.
    required_keys = ["username", "store", "card_data"]
    if not all(key in payload for key in required_keys):
        logger.error(f"Invalid 'availability_request' payload. Missing required keys. Payload: {payload}")
        return

    # If validation passes, proceed to queue the task.
    task_manager.queue_task(task_manager.task_definitions.UPDATE_AVAILABILITY_SINGLE_CARD, payload["username"], payload["store"], payload["card_data"])

def _handle_queue_all_availability_checks(payload: dict):
    username = payload.get("username")
    if not username:
        logger.error(f"Invalid 'queue_all_availability_checks' payload. Missing 'username'. Payload: {payload}")
        return

    # Delegate the fan-out logic to the existing task to keep the listener non-blocking.
    task_manager.queue_task(task_manager.task_definitions.UPDATE_WANTED_CARDS_AVAILABILITY, username)


HANDLER_MAP = {
    "availability_request": _handle_availability_request,
    "queue_all_availability_checks": _handle_queue_all_availability_checks,
}

class _Scheduler_Listener:
    """
    Manages a background thread to listen for results from workers on a Redis Pub/Sub channel.
    This is implemented as a singleton to ensure only one listener thread is active.
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
        logger.info("🎧 Scheduler results listener started. Subscribed to 'scheduler-requests' channel.")

        for message in self.pubsub.listen():
            try:
                data = json.loads(message["data"])
                command_type = data.get("type")
                handler = HANDLER_MAP.get(command_type)
                if handler:
                    payload = data.get("payload", {})
                    handler(payload)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON from scheduler-requests message: {e}. Message: {message.get('data')}")
            except Exception as e:
                logger.error(f"Error processing message in scheduler listener: {e}", exc_info=True)
        except Exception as e:
            # This block will be reached when self.pubsub.close() is called,
            # or if there's a connection error.
            logger.info(f"Scheduler listener loop exiting: {e}")

# Create a single instance of the listener.
_listener_instance = _Scheduler_Listener()

def start_scheduler_listener(app):
    """Public function to start the singleton worker listener."""
    _listener_instance.start()
