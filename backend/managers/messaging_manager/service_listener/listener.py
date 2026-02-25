from utility import logger
from typing import Callable
import threading
import json
import atexit
from managers import redis_manager


class Listener:
    """
    Manages a background thread to listen for results from
    workers on a Redis Pub/Sub channel.
    This is a generic implementation that can be instantiated
    for different services and channels.
    """

    def __init__(self, service_name: str, channel: str):
        self.thread = None
        self.pubsub = None
        self.service_name = service_name
        self.channel = channel
        self.dlq_name = f"{channel}-dlq"
        self.handler_map = {}

    def register_handler(self, command_type: str, handler: Callable):
        """Registers a handler for a specific command type."""
        self.handler_map[command_type] = handler

    def start(self):
        """Starts the listener thread if it's not already running."""
        if self.thread and self.thread.is_alive():
            logger.warning(f"{self.service_name} listener thread is already running.")
            return

        self.thread = threading.Thread(target=self._listen, daemon=True)
        self.thread.start()
        # Register the stop method to be called on application exit.
        atexit.register(self.stop)

    def stop(self):
        """Signals the listener thread to stop and cleans up resources."""
        logger.info(f"🛑 Shutting down {self.service_name} listener...")
        if self.pubsub:
            # This will cause the loop in _listen() to exit.
            self.pubsub.close()
        if self.thread:
            # Wait for the thread to finish cleanly.
            self.thread.join(timeout=5)
        logger.info(f"✅ {self.service_name} listener shut down gracefully.")

    def _listen(self):
        """The actual listener function that runs in the background thread."""
        self.pubsub = redis_manager.pubsub(ignore_subscribe_messages=True)
        if self.pubsub is None:
            logger.critical(f"{self.service_name} cannot talk on pubsub. Exiting")
            return
        self.pubsub.subscribe(self.channel)
        logger.info(
            f"🎧 {self.service_name} listener started. Subscribed to "
            f"'{self.channel}' channel."
        )

        try:
            for message in self.pubsub.listen():
                try:
                    data = json.loads(message["data"])
                    command_type = data.get("type")
                    handler = self.handler_map.get(command_type)
                    logger.debug(f"{self.service_name} "
                                 f"received message: {command_type}")
                    if handler:
                        payload = data.get("payload", {})
                        handler(payload)
                    else:
                        raise ValueError(f"No handler found for command type "
                                         f"'{command_type}' on "
                                         f"'{self.channel}' channel.")
                except Exception as e:
                    logger.error(
                        f"Failed to process {self.channel} message: {e}."
                        f" Message: {message.get('data')}"
                    )
                    try:
                        # Move the failed message to a dead-letter queue
                        redis_manager.get_redis_connection().rpush(
                            self.dlq_name, message.get("data")
                        )
                    except Exception as dlq_e:
                        logger.error(f"Failed to push message to DLQ: {dlq_e}")

        except Exception as e:
            # This block will be reached when self.pubsub.close() is called,
            # or if there's a connection error.
            logger.info(f"{self.service_name} listener loop exiting: {e}")
