import requests
from utility import logger
import gzip
from typing import List, Dict, Any, Generator
import ijson

from data.cache import cache_manager

# Cache external API calls for 24 hours to reduce load and improve performance.
CACHE_EXPIRATION_SECONDS = 24 * 60 * 60  # 24 hours


def fetch_scryfall_card_names() -> List[str]:
    """Fetches a list of all unique card names from Scryfall."""
    logger.info("Fetching card names from Scryfall...")
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
            cache_manager.save_data(
                cache_key, card_names, ex=CACHE_EXPIRATION_SECONDS
            )
            logger.info(f"✅ Cached {len(card_names)} card names for 24 hours.")
        return card_names
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch card names from Scryfall: {e}")
        return []


def fetch_all_sets() -> List[Dict[str, Any]]:
    """Fetches all set data from Scryfall."""
    cache_key = "scryfall_all_sets"
    cached_sets = cache_manager.load_data(cache_key)
    if cached_sets:
        logger.info(f"✅ Found {len(cached_sets)} sets in cache.")
        return cached_sets

    try:
        logger.info("🔄 Fetching card set information from Scryfall...")
        response = requests.get("https://api.scryfall.com/sets")
        response.raise_for_status()
        data = response.json()
        set_data = data.get("data", [])
        if set_data:
            cache_manager.save_data(
                cache_key, set_data, ex=CACHE_EXPIRATION_SECONDS
            )
            logger.info(f"✅ Cached {len(set_data)} sets for 24 hours.")
        return set_data
    except requests.exceptions.RequestException as e:
        logger.error(f"Request to Scryfall for set data failed: {e}")
        return []


def fetch_all_card_data() -> Generator[Dict[str, Any], None, None]:
    """
    Fetches the 'Default Cards' bulk data file from Scryfall. This file is
    a smaller collection of card printings. This function streams the data
    and yields each card object to avoid loading the entire file into memory.
    """
    try:
        logger.info("Fetching Scryfall bulk data catalog URL...")
        # First, get the list of bulk data files
        bulk_data_info_res = requests.get("https://api.scryfall.com/bulk-data")
        bulk_data_info_res.raise_for_status()
        bulk_data_info = bulk_data_info_res.json()

        # Find the 'Default Cards' data file URL
        default_cards_url = None
        for data_file in bulk_data_info.get("data", []):
            if data_file.get("type") == "default_cards":
                default_cards_url = data_file.get("download_uri")
                break

        if not default_cards_url:
            logger.error(
                "Could not find 'default_cards' download "
                "URI in Scryfall bulk data response."
            )
            return []

        logger.info(f"Downloading bulk data file from: {default_cards_url}")
        # Download the gzipped JSON file
        response = requests.get(default_cards_url, stream=True)
        response.raise_for_status()

        # Decompress on the fly and use ijson to parse the stream of objects.
        # The file is a single large array, so we target each 'item' in it.
        with gzip.open(response.raw, "rt", encoding="utf-8") as f:
            # ijson.items returns a generator, which we yield from.
            # This keeps memory usage low.
            logger.info("Successfully started streaming bulk card data.")
            yield from ijson.items(f, "item")

    except requests.exceptions.RequestException as e:
        logger.error(f"Request to Scryfall for bulk data failed: {e}")
    except Exception as e:
        logger.error(
            f"An unexpected error occurred during bulk data fetch: {e}"
        )
