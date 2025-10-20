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


def trigger_availability_check_for_card(username: str, card_data: dict, on_complete_callback: callable = None):
    """
    Forcefully triggers background availability checks for a single card against a user's preferred stores.
    This fulfills requirement [5.1.6] by always queueing a new check.
    """
    card_name = card_data.get("card_name")
    if not card_name:
        logger.error(f"Cannot trigger availability check; card_data is missing 'card_name'.")
        return

    logger.info(f"Triggering availability check for '{card_name}' for user '{username}'.")
    user_stores = database.get_user_stores(username)

    if not user_stores:
        logger.warning(f"User '{username}' has no preferred stores. Skipping automatic availability check.")
        return

    for store in user_stores:
        if not store or not store.slug:
            continue
        logger.debug(f"Queueing availability check for '{card_name}' at '{store.slug}'.")
        # Queue the background task using the task manager
        task_manager.queue_task(task_manager.task_definitions.UPDATE_AVAILABILITY_SINGLE_CARD, username, store.slug, card_data)
    
    # After queuing all tasks, call the callback if one was provided.
    # This is used to send the updated card list back to the user at the right time.
    if on_complete_callback:
        on_complete_callback()


def get_cached_availability_or_trigger_check(username: str) -> Dict[str, dict]:
    """
    Orchestrates the availability check for all of a user's tracked cards.
    It returns any data found in the cache and queues background tasks for any non-cached items.
    """
    user_stores = database.get_user_stores(username)
    user_cards = user_manager.load_card_list(username)

    if not user_stores:
        logger.warning(f"User '{username}' has no stores configured. Skipping availability check.")
        return {}

    cached_results = {}
    for card in user_cards:
        for store in user_stores:
            if not store or not store.slug or not card or not card.card_name:
                continue
            
            cached_data = availability_storage.get_cached_availability_data(store.slug, card.card_name)
            if cached_data is not None:
                logger.debug(f"✅ Cache hit for {card.card_name} at {store.name}.")
                cached_results.setdefault(store.slug, {})[card.card_name] = cached_data
            else:
                logger.info(f"⏳ Cache miss for {card.card_name} at {store.name}. Queueing check.")
                # Queue a task for only the specific card/store that missed the cache.
                task_manager.queue_task(task_manager.task_definitions.UPDATE_AVAILABILITY_SINGLE_CARD, username, store.slug, card.model_dump())

    return cached_results


def get_all_available_items_for_card(username: str, card_name: str) -> list:
    """
    Aggregates all available items for a single card from the cache across all of a user's preferred stores.
    This is used to populate the 'In Stock Details' modal on demand.
    """
    user_stores = database.get_user_stores(username)
    if not user_stores:
        logger.warning(f"User '{username}' has no stores configured. Cannot get stock data.")
        return []

    all_available_items = []
    for store in user_stores:
        # Fetch from cache
        cached_data = availability_storage.get_cached_availability_data(store.slug, card_name)
        if cached_data:  # cached_data is a list of item dicts
            # Add the store name to each item before adding it to the aggregated list.
            for item in cached_data:
                item_with_store = item.copy()
                item_with_store['store_name'] = store.name
                all_available_items.append(item_with_store)

    logger.info(f"Aggregated {len(all_available_items)} available items for '{card_name}' for user '{username}'.")
    return all_available_items
