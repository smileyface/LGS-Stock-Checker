import json

from managers.redis_manager.cache_manager.cache_manager import save_data, load_data
from utility.logger import logger


def cache_availability_data(store_name, card_name, available_items):
    """
    Cache availability results for a specific card at a store.
    """
    # Save availability data to Redis
    save_data(f"availability:{store_name}:{card_name}", available_items)
    logger.info(f"✅ Cached availability results for {card_name} at {store_name}")


def get_availability_data(store_name, card_name):
    """
    Retrieve availability data for a specific card at a store from Redis.
    """
    # Retrieve availability data from Redis
    cached_data = load_data(f"availability:{store_name}:{card_name}")
    if cached_data:
        return json.loads(cached_data)
    else:
        return None
