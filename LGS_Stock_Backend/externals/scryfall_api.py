import json
from typing import List, Dict, Any, Optional, Union

import requests
from data import cache
from utility import logger

SCRYFALL_CARD_CACHE_KEY = "scryfall_card_names"
SCRYFALL_CARD_CACHE_EXPIRY = 86400
SCRYFALL_SETS_API_URL = "https://api.scryfall.com/sets"


def fetch_scryfall_card_names() -> Optional[List[str]]:
    """
    Fetch all Magic: The Gathering card names from Scryfall and cache them.

    Returns:
        A list of card names, or None on failure.
    """
    cached_data = cache.load_data(SCRYFALL_CARD_CACHE_KEY)
    if cached_data:
        logger.info("✅ Loaded card names from cache.")
        return json.loads(cached_data)

    logger.info("🔄 Fetching card names from Scryfall...")
    url = "https://api.scryfall.com/catalog/card-names"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an exception for 4xx/5xx status codes

        card_names = response.json().get("data", [])
        logger.info(f"✅ Cached {len(card_names)} card names for 24 hours.")
        return card_names
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Failed to fetch Scryfall card names: {e}")
        return None


def fetch_all_sets() -> Optional[List[Dict[str, Any]]]:
    """
    Fetches all set data from the Scryfall API.

    Returns:
        A list of set data dictionaries, or None on failure.

    Logs:
        Logs any errors encountered during the request.
    """
    try:
        response = requests.get(SCRYFALL_SETS_API_URL)
        response.raise_for_status()
        return response.json().get("data")
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error fetching set data from Scryfall: {e}")
        return None
