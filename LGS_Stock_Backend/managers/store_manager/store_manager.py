from typing import Dict, List

from data import cache
from .stores import STORE_REGISTRY
from utility import logger


def load_store_availability(card_name: str, username: str = None) -> Dict[str, List[Dict]]:
    """
    Loads availability data for a card, checking cache first.
    If not cached, it scrapes all registered stores.
    """
    redis_key = f"store_availability_{card_name}"
    cached_data = cache.load_data(redis_key)
    if cached_data:
        logger.info(f"✅ Found cached availability for {card_name}")
        return cached_data

    logger.info(f"⚠️ No cache for {card_name}, scraping all stores.")
    availability = scrape_all_stores(card_name)

    # Cache the results
    cache.save_data(redis_key, availability, ex=1800)  # Cache for 30 minutes
    return availability


def scrape_all_stores(card_name: str) -> Dict[str, List[Dict]]:
    """Scrapes all registered stores for a given card's availability."""
    availability = {}
    for store_slug, store_impl in STORE_REGISTRY.items():
        try:
            results = store_impl.fetch_card_availability(card_name)
            if results:
                availability[store_slug] = results
        except Exception as e:
            logger.error(f"❌ Failed to scrape {store_slug} for {card_name}: {e}")
    return availability


def store_list(store_name: str = None):
    """Returns a specific store implementation or a list of all stores."""
    if store_name:
        return STORE_REGISTRY.get(store_name)
    return list(STORE_REGISTRY.values())