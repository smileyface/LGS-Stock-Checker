from typing import Dict

# Internal package imports
from . import availability_storage

# Manager package imports
from managers import user_manager
from managers import task_manager, socket_manager

# Project package imports
from data import database
from utility import logger


def check_availability(username: str) -> Dict[str, str]:
    """Manually triggers an availability update for a user's card list."""
    logger.info(f"🔄 User {username} requested a manual availability refresh.")
    task_manager.queue_task(task_manager.task_definitions.UPDATE_WANTED_CARDS_AVAILABILITY, username)
    return {"status": "queued", "message": "Availability update has been triggered."}


def get_card_availability(username):
    """
    Orchestrates the availability check for a user.

    This function iterates through a user's cards and stores, checks for cached
    availability data, and queues background tasks for any data that is not
    already cached. It returns the cached data it finds so the caller can
    immediately send it to the client.

    Returns:
        A dictionary of cached availability data, keyed by store slug and card name.
    """
    user_stores = database.get_user_stores(username)
    user_cards = user_manager.load_card_list(username)

    if not user_stores:
        logger.warning(f"User '{username}' has no stores configured. Skipping availability check.")
        return {}

    if not user_cards:
        logger.info(f"User '{username}' has no cards to check. Skipping availability check.")
        return {}

    cached_results = {}
    for store in user_stores:
        if not store or not store.slug:
            continue
        for card in user_cards:
            logger.debug(f"Checking cache for {card.card_name} at {store.name}")
            cached_data = availability_storage.get_availability_data(store.slug, card.card_name)
            if cached_data is None:
                # Fetch availability for the specific card at the store
                task_manager.queue_task(task_manager.task_definitions.UPDATE_AVAILABILITY_SINGLE_CARD, username, store.slug, card.model_dump())
                logger.info(f"⏳ Queued availability check for {card.card_name} at {store.name}.")
            else:
                logger.debug(f"✅ Cache hit for {card.card_name} at {store.name}.")
                cached_results.setdefault(store.slug, {})[card.card_name] = cached_data

    return cached_results
