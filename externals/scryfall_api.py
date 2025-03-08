import json

import requests

import managers.redis_manager as redis_manager
from utility.logger import logger

SCRYFALL_CARD_CACHE_KEY = "scryfall_card_names"
SCRYFALL_CARD_CACHE_EXPIRY = 86400


def fetch_scryfall_card_names():
    """Fetch all Magic: The Gathering card names from Scryfall and cache them."""
    cached_data = redis_manager.load_data(SCRYFALL_CARD_CACHE_KEY)
    if cached_data:
        logger.info("✅ Loaded card names from cache.")
        return json.loads(cached_data)
    else:
        logger.info("🔄 Fetching card names from Scryfall...")
        url = "https://api.scryfall.com/catalog/card-names"
        response = requests.get(url)

        if response.status_code == 200:
            card_names = response.json().get("data", [])
            if card_names:
                redis_manager.save_data(SCRYFALL_CARD_CACHE_KEY, json.dumps(card_names))
                logger.info(f"✅ Cached {len(card_names)} card names for 24 hours.")
                return card_names
            else:
                logger.warning("⚠️ Warning: Returning an empty list because Scryfall fetch failed.")
        else:
            logger.error(f"❌ Failed to fetch Scryfall data: {response.status_code}")
            return []
