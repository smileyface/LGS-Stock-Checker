import threading
import json
import atexit
from managers import (redis_manager,
                      availability_manager)
from data import database
from utility import logger


def _handle_availability_result(payload: dict):
    """
    Handler for processing 'availability_result' messages from workers.
    Caches the availability data.
    """
    if all(k in payload for k in ["store", "card", "items"]):
        logger.info(
            f"Received availability result for '{payload['card']}' at "
            f"'{payload['store']}' from worker."
        )
        availability_manager.cache_availability_data(
            payload["store"], payload["card"], payload["items"]
        )
    else:
        logger.error(f"Invalid availability result payload: {payload}")


def _handle_catalog_card_names_result(payload: dict):
    """Handler for 'catalog_card_names_result' from workers."""
    card_names = payload.get("names")
    if card_names and isinstance(card_names, list):
        logger.info(f"Received {len(card_names)} card names from worker.\
                     Updating database.")
        database.add_card_names_to_catalog(card_names)
    else:
        logger.error(f"Invalid card names payload: {payload}")


def _handle_catalog_set_data_result(payload: dict):
    """Handler for 'catalog_set_data_result' from workers."""
    set_data = payload.get("sets")
    if set_data and isinstance(set_data, list):
        logger.info(f"Received {len(set_data)} sets from worker. \
                    Updating database.")
        database.add_set_data_to_catalog(set_data)
    else:
        logger.error(f"Invalid set data payload: {payload}")


def _handle_catalog_finishes_result(payload: dict):
    """Handler for 'catalog_finishes_result' from workers."""
    finishes = payload.get("finishes")
    if finishes and isinstance(finishes, list):
        logger.info(f"Received {len(finishes)} finishes from worker. \
                    Updating database.")
        database.bulk_add_finishes(finishes)
    else:
        logger.error(f"Invalid finishes payload: {payload}")


def _handle_catalog_printings_chunk_result(payload: dict):
    """Handler for a chunk of card printings from workers."""
    printings_chunk = payload.get("printings")
    if not printings_chunk or not isinstance(printings_chunk, list):
        logger.error(f"Invalid printings chunk payload: {payload}")
        return

    logger.info(f"Processing chunk of {len(printings_chunk)} printings\
                 from worker.")
    # This logic is moved from the old `_process_catalog_chunk` helper
    printings_to_add = [
        {k:
         v for k,
         v in p.items() if k != "finishes"} for p in printings_chunk
    ]
    database.bulk_add_card_printings(printings_to_add)

    # Now handle the associations
    printings_map = database.get_all_printings_map()
    finishes_map = database.get_all_finishes_map()
    associations_to_add = []
    for card in printings_chunk:
        printing_key = (card.get("card_name"),
                        card.get("set_code"),
                        card.get("collector_number"))
        printing_id = printings_map.get(printing_key)
        if printing_id:
            for finish_name in card.get("finishes", []):
                finish_id = finishes_map.get(finish_name)
                if finish_id:
                    associations_to_add.append({"printing_id": printing_id,
                                                "finish_id": finish_id})

    if associations_to_add:
        database.bulk_add_printing_finish_associations(associations_to_add)


# A map of event types to their corresponding handler functions.
HANDLER_MAP = {
    "availability_result": _handle_availability_result,
    "catalog_card_names_result": _handle_catalog_card_names_result,
    "catalog_set_data_result": _handle_catalog_set_data_result,
    "catalog_finishes_result": _handle_catalog_finishes_result,
    "catalog_printings_chunk_result": _handle_catalog_printings_chunk_result,
}


class _Server_Listener:
    """
    Manages a background thread on the server to listen for results from
    workers on a Redis Pub/Sub channel.
    This is implemented as a singleton to ensure only one listener
    thread is active.
    """

    def __init__(self):
        self.thread = None
        self.pubsub = None

    def start(self):
        """Starts the listener thread if it's not already running."""
        if self.thread and self.thread.is_alive():
            logger.warning("Server listener thread is already running.")
            return

        self.thread = threading.Thread(target=self._listen, daemon=True)
        self.thread.start()
        # Register the stop method to be called on application exit.
        atexit.register(self.stop)

    def stop(self):
        """Signals the listener thread to stop and cleans up resources."""
        logger.info("🛑 Shutting down server listener...")
        if self.pubsub:
            # This will cause the loop in _listen() to exit.
            self.pubsub.close()
        if self.thread:
            # Wait for the thread to finish cleanly.
            self.thread.join(timeout=5)
        logger.info("✅ Server listener shut down gracefully.")

    def _listen(self):
        """The actual listener function that runs in the background thread."""
        self.pubsub = redis_manager.pubsub(ignore_subscribe_messages=True)
        self.pubsub.subscribe("worker-results")
        logger.info(
            "🎧 Server results listener started. Subscribed to "
            "'worker-results' channel."
        )
        try:
            for message in self.pubsub.listen():
                try:
                    data = json.loads(message["data"])
                    event_type = data.get("type")
                    handler = HANDLER_MAP.get(event_type)
                    logger.debug(f"Server recieved message from worker: "
                                 f"{event_type}")
                    if handler:
                        payload = data.get("payload", {})
                        handler(payload)
                    else:
                        logger.warning(
                            f"No handler found for event type '{event_type}' "
                            f"on 'worker-results' channel. Payload: {data}"
                        )
                except Exception as e:
                    logger.error(
                        f"Error processing message in server listener: {e}",
                        exc_info=True,
                    )
                    try:
                        # Move the failed message to a dead-letter queue
                        # for worker results
                        redis_manager.get_redis_connection().rpush(
                            "worker-results-dlq", message.get("data")
                        )
                    except Exception as dlq_e:
                        logger.error(f"Failed to push message to DLQ: {dlq_e}")
        except Exception as e:
            # This block will be reached when self.pubsub.close() is called,
            # or if there's a connection error.
            logger.info(f"Server listener loop exiting: {e}")


_listener_instance = _Server_Listener()


# Create a single instance of the listener.
def start_server_listener(app):
    """Public function to start the singleton server listener."""
    _listener_instance.start()
