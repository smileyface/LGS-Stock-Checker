import requests
from utility import logger
import json
import gzip
from typing import List, Dict, Any

from data.cache import cache_manager


def fetch_scryfall_card_names() -> List[str]:
    """Fetches a list of all unique card names from Scryfall."""
    cache_key = "scryfall_card_names"
    cached_names = cache_manager.load_data(cache_key)
    if cached_names:
        logger.info(f"✅ Found {len(cached_names)} card names in cache.")
        return cached_names

    try:
        logger.info("🔄 Fetching card names from Scryfall...")
        response = requests.get("https://api.scryfall.com/catalog/card-names")
        response.raise_for_status()
        data = response.json()
        card_names = data.get("data", [])
        if card_names:
            cache_manager.save_data(cache_key, card_names, expiration_hours=24)
            logger.info(f"✅ Cached {len(card_names)} card names for 24 hours.")
        return card_names
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch card names from Scryfall: {e}")
        return []


def fetch_all_sets() -> List[Dict[str, Any]]:
    """Fetches all set data from Scryfall."""
    try:
        logger.info("Fetching card set information from Scryfall...")
        response = requests.get("https://api.scryfall.com/sets")
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])
    except requests.exceptions.RequestException as e:
        logger.error(f"Request to Scryfall for set data failed: {e}")
        return []


def fetch_all_card_data() -> List[Dict[str, Any]]:
    """
    Fetches the 'All Cards' bulk data file from Scryfall, which contains
    an object for every printing of every card.
    """
    try:
        logger.info("Fetching Scryfall bulk data catalog URL...")
        # First, get the list of bulk data files
        bulk_data_info_res = requests.get("https://api.scryfall.com/bulk-data")
        bulk_data_info_res.raise_for_status()
        bulk_data_info = bulk_data_info_res.json()

        # Find the 'All Cards' data file URL
        all_cards_url = None
        for data_file in bulk_data_info.get("data", []):
            if data_file.get("type") == "all_cards":
                all_cards_url = data_file.get("download_uri")
                break

        if not all_cards_url:
            logger.error("Could not find 'all_cards' download URI in Scryfall bulk data response.")
            return []

        logger.info(f"Downloading bulk data file from: {all_cards_url}")
        # Download the gzipped JSON file
        response = requests.get(all_cards_url, stream=True)
        response.raise_for_status()

        # Decompress and parse the JSON data
        card_data = []
        # The 'with' statement ensures the file handle is closed properly.
        # We decompress on the fly and load the JSON.
        with gzip.open(response.raw, 'rt', encoding='utf-8') as f:
            card_data = json.load(f)

        logger.info(f"Successfully downloaded and parsed {len(card_data)} card printings.")
        return card_data

    except requests.exceptions.RequestException as e:
        logger.error(f"Request to Scryfall for bulk data failed: {e}")
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred during bulk data fetch: {e}")
        return []