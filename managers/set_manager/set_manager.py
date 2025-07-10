import json
import os
import time
from typing import Dict, Optional

from externals import scryfall_api
from utility.logger import logger

# --- Configuration ---
SET_LOOKUP_FILE = "set_lookup.json"
SET_UPDATE_INTERVAL = 86400  # 24 hours in seconds

# --- In-memory cache ---
_SET_NAME_TO_CODE: Dict[str, str] = {}
_SET_CODE_TO_NAME: Dict[str, str] = {}


def _load_set_data_from_file() -> bool:
    """Loads the set lookup data from the JSON file into memory."""
    global _SET_NAME_TO_CODE, _SET_CODE_TO_NAME
    try:
        with open(SET_LOOKUP_FILE, "r") as file:
            set_data = json.load(file)
        _SET_NAME_TO_CODE = {name: code.upper() for name, code in set_data.items()}
        _SET_CODE_TO_NAME = {code.upper(): name for name, code in set_data.items()}
        logger.info("✅ Set data loaded into memory from file.")
        return True
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not load set data from {SET_LOOKUP_FILE}: {e}")
        return False


def _save_set_data_to_file() -> None:
    """Fetches fresh set data from Scryfall and saves it to the JSON file."""
    global _SET_NAME_TO_CODE, _SET_CODE_TO_NAME
    logger.info("⏳ Fetching fresh set data from Scryfall API...")
    sets = scryfall_api.fetch_all_sets()

    if not sets:
        logger.error("❌ Failed to fetch set data from Scryfall. In-memory data may be stale.")
        return

    set_data = {s["name"]: s["code"].upper() for s in sets if "code" in s and "name" in s}

    try:
        with open(SET_LOOKUP_FILE, "w") as file:
            json.dump(set_data, file, indent=4)
        logger.info(f"✅ Set data fetched and saved to {SET_LOOKUP_FILE}.")
        _SET_NAME_TO_CODE = {name: code.upper() for name, code in set_data.items()}
        _SET_CODE_TO_NAME = {code.upper(): name for name, code in set_data.items()}
    except IOError as e:
        logger.error(f"❌ Error saving set data to {SET_LOOKUP_FILE}: {e}")


def initialize_set_data():
    """Initializes the set data cache on application startup."""
    if not os.path.exists(SET_LOOKUP_FILE) or \
       (time.time() - os.path.getmtime(SET_LOOKUP_FILE) > SET_UPDATE_INTERVAL):
        logger.info("Set lookup file is missing or outdated. Fetching fresh data.")
        _save_set_data_to_file()
    else:
        logger.info("Set lookup table is up to date. Loading from file.")
        if not _load_set_data_from_file():
            _save_set_data_to_file()  # Fetch if loading failed


def is_set_code(value: str) -> bool:
    """Checks if a given value is a valid set code."""
    return value.upper() in _SET_CODE_TO_NAME


def is_set_name(value: str) -> bool:
    """Checks if a given value is a valid set name."""
    return value in _SET_NAME_TO_CODE


def set_code(value: str) -> Optional[str]:
    """Returns the set code corresponding to a set name or set code."""
    if not value: return None
    return _SET_NAME_TO_CODE.get(value, value.upper() if is_set_code(value) else None)


def set_name(value: str) -> Optional[str]:
    """Returns the set name corresponding to a set code or set name."""
    if not value: return None
    return _SET_CODE_TO_NAME.get(value.upper(), value if is_set_name(value) else None)
