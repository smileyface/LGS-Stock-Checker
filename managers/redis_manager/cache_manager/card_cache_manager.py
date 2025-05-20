import json

from managers.redis_manager.cache_manager.cache_manager import save_data, load_data
from utility.logger import logger

def _availability_cache_name(card_name):
    """
    Generate a unique cache name for availability data based on card name.
    """
    return f"availability:{card_name}"

def cache_availability_data(card_name, available_items):
    """
    Cache availability results for a specific card at a store.
    """
    # Save availability data to Redis
    save_data(_availability_cache_name(card_name), available_items)
    logger.info(f"✅ Cached availability results for {card_name}")


def get_availability_data(card_name):
    """
    Retrieve availability data for a specific card at a store from Redis.
    """
    # Retrieve availability data from Redis
    cached_data = load_data(_availability_cache_name(card_name))
    if cached_data:
        return json.loads(cached_data)
    else:
        return None
