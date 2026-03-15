from managers import availability_manager
from data import database
from utility import logger
from .listener import Listener


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

    # First, add all unique finishes to the database
    finishes_in_chunk = {finish for card in printings_chunk
                         for finish in card.get("finishes", [])}
    if finishes_in_chunk:
        database.bulk_add_finishes(list(finishes_in_chunk))

    # Next, add the card printings themselves
    printings_to_add = [
        {k:
         v for k,
         v in p.items() if k != "finishes"} for p in printings_chunk
    ]
    database.bulk_add_card_printings(printings_to_add)


# A map of event types to their corresponding handler functions.
HANDLER_MAP = {
    "availability_result": _handle_availability_result,
    "catalog_card_names_result": _handle_catalog_card_names_result,
    "catalog_set_data_result": _handle_catalog_set_data_result,
    "catalog_finishes_result": _handle_catalog_finishes_result,
    "catalog_finishes_chunk_result": _handle_catalog_finishes_result,
    "catalog_printings_chunk_result": _handle_catalog_printings_chunk_result,
}


# Create a single instance of the listener.
_listener_instance = Listener(service_name="Server", channel="worker-results")
for command, handler in HANDLER_MAP.items():
    _listener_instance.register_handler(command, handler)


# Create a single instance of the listener.
def start_server_listener(app):
    """Public function to start the singleton server listener."""
    _listener_instance.start()
