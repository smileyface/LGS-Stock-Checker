from managers.redis_manager import redis_manager
from managers.store_manager import cache_handler, get_cached_availability, store_availability_in_cache
from managers.store_manager.store_manager import STORE_REGISTRY
from managers.user_manager.user_preferences import get_selected_stores
from managers.user_manager.user_cards import load_card_list
from utility.logger import logger

def check_availability(username):
    """Manually triggers an availability update for a user's card list."""
    logger.info(f"🔄 User {username} requested a manual availability refresh.")

    redis_manager.queue_task("update_wanted_cards_availability", username)

    return {"status": "queued", "message": "Availability update has been triggered."}


def get_total_availability(username):
    """
    Retrieves the full availability dataset for a user's tracked cards,
    only querying the stores they have selected.

    Args:
        username (str): The username of the person requesting availability.

    Returns:
        dict: Availability data structured by store, then by card.
    """
    logger.info(f"🔍 Fetching total availability for user: {username}")

    # Step 1: Get user-selected stores
    selected_stores = get_selected_stores(username)
    if not selected_stores:
        logger.warning(f"🚨 No stores selected for user {username}. Returning empty availability.")
        return {}

    # Step 2: Get the user's tracked card list
    user_cards = load_card_list(username)
    if not user_cards:
        logger.warning(f"🚨 User {username} has no tracked cards. Returning empty availability.")
        return {}

    total_availability = {}  # Store structured results

    # Step 3: Iterate only through the selected stores
    for store_name in selected_stores:
        store_obj = STORE_REGISTRY[store_name]  # Get the store object dynamically
        if not store_obj:
            logger.warning(f"🚨 Store '{store_name}' not found. Skipping.")
            continue

        store_results = {}  # Store results per store

        for card in user_cards:
            card_name = card["card_name"]

            # Step 4: Use `get_single_card_availability` to handle caching & fetching logic
            availability = get_single_card_availability(card, store_obj)
            if availability:
                store_results[card_name] = availability  # Save results for the store

        if store_results:
            total_availability[store_name] = store_results  # Add store's results

    logger.info(f"📊 Finished fetching availability for user: {username}")
    return total_availability  # Returns all available data

def get_single_card_availability(username, card_name):
    """Fetches availability **only** from the stores the user has selected."""
    user_stores = get_selected_stores(username)  # Fetch user's selected stores
    logger.info(f"🔍 User {username} is checking {card_name} in stores: {user_stores}")

    # Filter out only selected stores from the cache
    cached_availability = cache_handler.get_cached_availability(card_name)

    if cached_availability and len(cached_availability) == len(user_stores):
        return cached_availability  # ✅ If all selected stores are fresh, return immediately

    # Identify stores needing fresh data
    stores_to_check = [store for store in user_stores if store not in cached_availability]
    fresh_data = {}

    for store in stores_to_check:
        fresh_data[store] = store.check_availability(card_name)

        # Update cache per store
        cache_handler.store_availability_in_cache(card_name, store, fresh_data[store])

    # Combine fresh and cached results, ensuring only user-selected stores are returned
    return {**cached_availability, **fresh_data}
