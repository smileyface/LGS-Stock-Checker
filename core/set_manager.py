import json
import os
import time
import requests
from config.settings import SET_LOOKUP_FILE, SCRYFALL_SETS_API, SET_UPDATE_INTERVAL
from utility.logger import logger

# Global variables for in-memory lookups
SET_NAME_TO_CODE = {}
SET_CODE_TO_NAME = {}

def load_set_data():
    """
    Loads the set lookup data from the file into memory.
    """
    global SET_NAME_TO_CODE, SET_CODE_TO_NAME
    try:
        with open(SET_LOOKUP_FILE, "r") as file:
            set_data = json.load(file)

        # Populate both name-to-code and code-to-name mappings
        SET_NAME_TO_CODE = {name: code.upper() for name, code in set_data.items()}
        SET_CODE_TO_NAME = {code.upper(): name for name, code in set_data.items()}
        logger.info("Set data loaded into memory.")

    except FileNotFoundError:
        logger.warning(f"Set lookup file '{SET_LOOKUP_FILE}' not found. Fetching fresh data from Scryfall...")
        fetch_and_save_set_data()
    except json.JSONDecodeError:
        logger.error(f"Set lookup file '{SET_LOOKUP_FILE}' is corrupted. Fetching fresh data from Scryfall...")
        fetch_and_save_set_data()

def fetch_and_save_set_data():
    """
    Fetches set data from the Scryfall API and saves it to the set lookup file.
    """
    global SET_NAME_TO_CODE, SET_CODE_TO_NAME
    try:
        response = requests.get(SCRYFALL_SETS_API)
        response.raise_for_status()
        sets = response.json()["data"]

        # Build the lookup table
        set_data = {set["name"]: set["code"].upper() for set in sets}

        # Save to file
        with open(SET_LOOKUP_FILE, "w") as file:
            json.dump(set_data, file, indent=4)
        
        logger.info(f"Set data fetched and saved to {SET_LOOKUP_FILE}.")

        # Populate in-memory lookups
        SET_NAME_TO_CODE = {name: code.upper() for name, code in set_data.items()}
        SET_CODE_TO_NAME = {code.upper(): name for name, code in set_data.items()}
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data from Scryfall: {e}")
    except Exception as e:
        logger.error(f"Error saving set data: {e}")

def update_set_data():
    """
    Updates the set lookup table if the last update exceeds the update interval.
    """
    if not os.path.exists(SET_LOOKUP_FILE):
        logger.warning("Set lookup file not found. Fetching data from Scryfall...")
        fetch_and_save_set_data()
        return

    last_modified = os.path.getmtime(SET_LOOKUP_FILE)
    current_time = time.time()
    if current_time - last_modified > SET_UPDATE_INTERVAL:
        logger.info("Set lookup table is outdated. Fetching updated data from Scryfall...")
        fetch_and_save_set_data()
    else:
        logger.info("Set lookup table is up to date.")
        load_set_data()

def is_set_code(value):
    """
    Checks if a given value is a valid set code.
    """
    return value.upper() in SET_CODE_TO_NAME

def is_set_name(value):
    """
    Checks if a given value is a valid set name.
    """
    return value in SET_NAME_TO_CODE

def set_code(value):
    """
    Returns the set code corresponding to a set name or set code.
    """
    value_upper = value.upper()
    if is_set_code(value_upper):
        return value_upper
    return SET_NAME_TO_CODE.get(value, None)

def set_name(value):
    """
    Returns the set name corresponding to a set code or set name.
    """
    value_upper = value.upper()
    if is_set_name(value):
        return value
    return SET_CODE_TO_NAME.get(value_upper, None)
