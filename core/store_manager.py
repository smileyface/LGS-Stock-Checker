import os
import time

from core.user_manager import load_json, save_json
from stores.authority_games_mesa_az import Authority_Games_Mesa_Arizona

STORE_REGISTRY = {
    "Authority_Games_Mesa_Arizona": Authority_Games_Mesa_Arizona()
}

def save_store_availability(store_name, card_name, listings):
    """Save store availability data with a timestamp."""
    store_file = os.path.join("data/store", f"{store_name}.json")
    
    if not os.path.exists("data/store"):
        os.makedirs("data/store", exist_ok=True)

    # Load existing data if available
    store_data = load_json(store_file) or {}

    # Update the entry with a new timestamp
    store_data[card_name] = {
        "last_updated": int(time.time()),
        "listings": listings
    }

    save_json(store_data, store_file)

def load_store_availability(store_name):
    """Load all stored availability data for a given store."""
    store_file = os.path.join("data/store", f"{store_name}.json")
    return load_json(store_file) or {}