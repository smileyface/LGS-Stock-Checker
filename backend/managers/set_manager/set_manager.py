import json
import os
import time
from typing import Optional

from bidict import bidict

from externals import scryfall_api
from utility import logger

# --- Configuration ---
# Construct a robust path to the file, assuming it's in the parent directory
# of 'managers'
_BACKEND_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
SET_LOOKUP_FILE = os.path.join(_BACKEND_DIR, "set_lookup.json")
SET_UPDATE_INTERVAL = 86400  # 24 hours in seconds

# --- In-memory cache ---
_set_map: bidict[str, str] = bidict()
_initialized = False


def _load_set_data_from_file() -> bool:
    """Loads the set lookup data from the JSON file into memory."""
    global _set_map
    try:
        with open(SET_LOOKUP_FILE, "r") as file:
            set_data = json.load(file)
        _set_map.clear()
        _set_map.update({name: code.upper() for name, code
                         in set_data.items()})
        logger.info("✅ Set data loaded into memory from file.")
        return True
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not load set data from {SET_LOOKUP_FILE}: {e}")
        return False


def _save_set_data_to_file() -> None:
    """Fetches fresh set data from Scryfall and saves it to the JSON file."""
    global _set_map
    logger.info("⏳ Fetching fresh set data from Scryfall API...")
    sets = scryfall_api.fetch_all_sets()

    if not sets:
        logger.error(
            "❌ Failed to fetch set data from Scryfall. "
            "In-memory data may be stale."
        )
        return

    set_data = {
        s["name"]: s["code"].upper()
        for s in sets
        if "code" in s and "name" in s
    }

    try:
        with open(SET_LOOKUP_FILE, "w") as file:
            json.dump(set_data, file, indent=4)
        logger.info(f"✅ Set data fetched and saved to {SET_LOOKUP_FILE}.")
        # Update the in-memory bidict after saving
        _set_map.clear()
        _set_map.update({name: code.upper() for name, code
                         in set_data.items()})
    except IOError as e:
        logger.error(f"❌ Error saving set data to {SET_LOOKUP_FILE}: {e}")


def initialize_set_data():
    """Initializes the set data cache on application startup."""
    global _initialized
    if _initialized:
        return

    if not os.path.exists(SET_LOOKUP_FILE) or (
        time.time() - os.path.getmtime(SET_LOOKUP_FILE) > SET_UPDATE_INTERVAL
    ):
        logger.info(
            "Set lookup file is missing or outdated. Fetching fresh data."
        )
        _save_set_data_to_file()
    else:
        logger.info("Set lookup table is up to date. Loading from file.")
        if not _load_set_data_from_file():
            _save_set_data_to_file()  # Fetch if loading failed
    _initialized = True


def is_set_code(value: str) -> bool:
    """Checks if a given value is a valid set code (case-insensitive)."""
    return value.upper() in _set_map.inverse


def is_set_name(value: str) -> bool:
    """Checks if a given value is a valid set name (case-sensitive)."""
    return value in _set_map


def set_code(value: str) -> Optional[str]:
    """Returns the set code corresponding to a set name or set code."""
    if not value:
        return None
    # Prioritize name lookup (case-sensitive)
    code = _set_map.get(value)
    if code:
        return code
    # If not a name, check if it's a valid code (case-insensitive)
    if value.upper() in _set_map.inverse:
        return value.upper()
    return None


def set_name(value: str) -> Optional[str]:
    """Returns the set name corresponding to a set code or set name."""
    if not value:
        return None
    # Prioritize code lookup (case-insensitive)
    name = _set_map.inverse.get(value.upper())
    if name:
        return name
    # If not a code, check if it's a valid name (case-sensitive)
    if value in _set_map:
        return value
    return None
