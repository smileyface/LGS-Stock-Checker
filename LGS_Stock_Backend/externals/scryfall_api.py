import json
from typing import List, Dict, Any, Optional

import requests

import data
from utility.logger import logger

SCRYFALL_CARD_CACHE_KEY = "scryfall_card_names"
SCRYFALL_CARD_CACHE_EXPIRY = 86400
SCRYFALL_SETS_API_URL = "https://api.scryfall.com/sets"


def fetch_scryfall_card_names():
    """Fetch all Magic: The Gathering card names from Scryfall and cache them."""
    # Use the data layer for caching to avoid circular dependencies
    cached_data = data.load_data(SCRYFALL_CARD_CACHE_KEY)
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
                data.save_data(SCRYFALL_CARD_CACHE_KEY, json.dumps(card_names), ex=SCRYFALL_CARD_CACHE_EXPIRY)
                logger.info(f"✅ Cached {len(card_names)} card names for 24 hours.")
                return card_names
            else:
                logger.warning("⚠️ Warning: Returning an empty list because Scryfall fetch failed.")
        else:
            logger.error(f"❌ Failed to fetch Scryfall data: {response.status_code}")
            return []


def fetch_all_sets() -> Optional[List[Dict[str, Any]]]:
    """
    Fetches all set data from the Scryfall API.

    Returns:
        A list of set data dictionaries, or None on failure.
    """
    try:
        response = requests.get(SCRYFALL_SETS_API_URL)
        response.raise_for_status()
        return response.json().get("data")
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error fetching set data from Scryfall: {e}")
        return None
