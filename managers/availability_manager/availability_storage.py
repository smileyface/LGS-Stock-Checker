import json

import managers.redis_manager as redis_manager
from utility.logger import logger

CACHE_EXPIRY = 1800  # Cache availability results for 30 minutes

def _availability_cache_name(store_name, card_name):
    """
    Generate a unique cache name for availability data based on card name.
    """
    return f"availability:{store_name}:{card_name}"


def cache_availability_data(store_name, card_name, available_items):
    """
    Cache availability results for a specific card at a store for 30 minutes.
    """
    # Save availability data to Redis
    redis_manager.cache_manager.save_data(_availability_cache_name(store_name, card_name), available_items, ex=CACHE_EXPIRY)
    logger.info(f"✅ Cached availability results for {card_name}")


def get_availability_data(store_name, card_name):
    """
    Retrieve availability data for a specific card at a store from Redis.
    """
    # Retrieve availability data from Redis
    cached_data = redis_manager.cache_manager.load_data(_availability_cache_name(store_name, card_name))
    if cached_data:
        return json.loads(cached_data)
    else:
        return None
