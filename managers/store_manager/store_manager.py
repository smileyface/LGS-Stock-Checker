import json
import time

from managers.store_manager import get_cached_availability, store_availability_in_cache
from stores.authority_games_mesa_az import Authority_Games_Mesa_Arizona
from utility.logger import logger

STORE_REGISTRY = {
    "Authority_Games_Mesa_Arizona": Authority_Games_Mesa_Arizona()
}

CACHE_EXPIRY_SECONDS = 3600  # 1 hour

def get_card_data(card, store):
    """
    Retrieves availability data for a given card across stores.

    Args:
        card (dict): The card's details (name, set, finish, etc.).
        store (Store): A store instance to query.

    Returns:
        dict: Full cached availability data for the card.
    """
    card_name = card["card_name"]

    # Step 1: Check Cache using get_cached_availability
    cached_data = get_cached_availability(card_name)  # Pull all cached stores for this card
    store_name = store.store_name

    if cached_data and store_name in cached_data:
        store_data = json.loads(cached_data[store_name])
        last_checked = store_data.get("last_checked", 0)

        # Step 2: Use fresh cache data if valid
        if time.time() - last_checked < CACHE_EXPIRY_SECONDS:
            logger.info(f"🔍 Cache hit for {card_name} at {store_name}. Returning cached data.")
            return cached_data  # Return entire cached dataset

    # Step 3: Cache miss or stale -> Fetch new data
    logger.info(f"🔄 Fetching {card_name} from {store_name}. Cache expired or not found.")
    store_results = store.check_availability(card)

    # Step 4: Store new data using `store_availability_in_cache()`
    store_availability_in_cache(card_name, store_name, store_results)  # Save to cache

    # Step 5: Retrieve updated cache and return full dataset
    updated_cache = get_cached_availability(card_name)
    return updated_cache