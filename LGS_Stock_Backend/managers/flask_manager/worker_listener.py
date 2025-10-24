import threading
import json
import atexit
from managers import redis_manager, availability_manager
from utility import logger


class _WorkerListener:
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
            logger.warning("Worker listener thread is already running.")
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
        logger.info("✅ Worker results listener shut down gracefully.")

    def _listen(self):
        """The actual listener function that runs in the background thread."""
        self.pubsub = redis_manager.pubsub(ignore_subscribe_messages=True)
        self.pubsub.subscribe("worker-results")
        logger.info("🎧 Worker results listener started. Subscribed to 'worker-results' channel.")

        try:
            for message in self.pubsub.listen():
                data = json.loads(message["data"])
                event_type = data.get("type")

                if event_type == "availability_result":
                    payload = data.get("payload", {})
                    if all(k in payload for k in ["store", "card", "items"]):
                        logger.info(f"Received availability result for '{payload['card']}' at '{payload['store']}' from worker.")
                        availability_manager.cache_availability_data(payload['store'], payload['card'], payload['items'])
                    else:
                        logger.error(f"Invalid availability result payload: {payload}")
        except Exception as e:
            # This block will be reached when self.pubsub.close() is called,
            # or if there's a connection error.
            logger.info(f"Worker listener loop exiting: {e}")

# Create a single instance of the listener.
_listener_instance = _WorkerListener()

def start_worker_listener(app):
    """Public function to start the singleton worker listener."""
    _listener_instance.start()