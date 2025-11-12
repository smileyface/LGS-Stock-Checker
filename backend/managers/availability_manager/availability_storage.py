import json

from data import cache
from utility import logger

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
    cache.save_data(
        _availability_cache_name(store_name, card_name),
        available_items,
        ex=CACHE_EXPIRY,
    )
    logger.info(f"✅ Cached availability results for {card_name}")


def get_cached_availability_data(store_name, card_name):
    """
    Retrieve availability data for a specific card at a store from Redis.
    """
    # Retrieve availability data from Redis
    # The cache.load_data function already handles JSON deserialization.
    return cache.load_data(_availability_cache_name(store_name, card_name))
