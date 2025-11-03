import threading
import json
import atexit
from managers import redis_manager, task_manager
from data import cache, database
from utility import logger


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

        try:
            for message in self.pubsub.listen():
                data = json.loads(message["data"])
                event_type = data.get("type")

                if event_type == "availability_request":
                    all_cards = database.get_all_tracked_cards()
                    
        except Exception as e:
            # This block will be reached when self.pubsub.close() is called,
            # or if there's a connection error.
            logger.info(f"Scheduler listener loop exiting: {e}")

# Create a single instance of the listener.
_listener_instance = _Scheduler_Listener()

def start_scheduler_listener(app):
    """Public function to start the singleton worker listener."""
    _listener_instance.start()
