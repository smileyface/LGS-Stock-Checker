import json
from datetime import datetime

from managers.redis_manager import redis_manager
from utility.logger import logger


def get_cached_availability(card_name):
    """Retrieves cached availability data for only the user's selected stores."""
    redis_key = f"availability_{card_name}"
    cached_data = redis_manager.get_all_hash_fields(redis_key)

    if not cached_data:
        logger.info(f"🔍 Cache miss for {card_name}. Fetching from stores.")
        return {}  # Empty dictionary instead of None

    return cached_data


def store_availability_in_cache(card_name, store_name, availability_data):
    """Stores the latest availability data for a specific card from a store in the cache."""

    redis_key = f"availability_{card_name}"  # Cache key based on card name

    # Ensure store_name is a string
    if not isinstance(store_name, str):
        logger.warning(f"🚨 store_name should be a string but got {type(store_name)}: {store_name}")
        if hasattr(store_name, "store_name"):
            store_name = store_name.store_name
            logger.info(f"🔄 Converted store_name to string: {store_name}")
        else:
            raise TypeError(f"❌ store_name must be a string, got {type(store_name)}")

    # Structure the data with a timestamp
    cache_entry = {
        "available": availability_data,  # List of available stock details
        "last_checked": datetime.utcnow().isoformat()  # Store timestamp in ISO format
    }

    logger.debug(f"💾 Preparing to cache availability for {card_name} at {store_name}. Data: {cache_entry}")

    try:
        # Convert to JSON and store in Redis hash
        json_entry = json.dumps(cache_entry)
        redis_manager.set_hash_field(redis_key, store_name, json_entry)

        logger.info(f"✅ Successfully cached availability for {card_name} from {store_name}.")
    except TypeError as e:
        logger.error(f"❌ JSON serialization error: {e}. Data: {cache_entry}")
        raise

