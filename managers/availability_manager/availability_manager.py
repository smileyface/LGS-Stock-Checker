from managers.redis_manager import redis_manager
from managers.store_manager import cache_handler
from managers.user_manager.user_preferences import get_selected_stores
from utility.logger import logger

def check_availability(username):
    """Manually triggers an availability update for a user's card list."""
    logger.info(f"🔄 User {username} requested a manual availability refresh.")

    redis_manager.queue_task("update_wanted_cards_availability", username)

    return {"status": "queued", "message": "Availability update has been triggered."}


def get_single_card_availability(username, card_name):
    """Fetches availability **only** from the stores the user has selected."""
    user_stores = get_selected_stores(username)  # Fetch user's selected stores
    logger.info(f"🔍 User {username} is checking {card_name} in stores: {user_stores}")

    # Filter out only selected stores from the cache
    cached_availability = cache_handler.get_cached_availability(card_name, user_stores)

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
