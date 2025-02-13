import json
import os
from managers.availability_manager.availability_storage import load_availability, save_availability
from managers.availability_manager.availability_diff import detect_changes
from managers.redis_manager import redis_manager
from managers.user_manager.user_manager import load_card_list
from utility.logger import logger

def check_availability(username):
    """Manually triggers an availability update for a user's card list."""
    logger.info(f"🔄 User {username} requested a manual availability refresh.")

    redis_manager.queue_task("update_wanted_cards_availability", username)

    return {"status": "queued", "message": "Availability update has been triggered."}


def get_card_availability(username):
    """Fetches a list of user cards that are available in stores."""
    redis_key = f"{username}_availability_results"
    availability_data = redis_manager.get_all_hash_fields(redis_key) # Fetch all availability data

    # Convert stored JSON strings back into Python objects
    parsed_data = {key: json.loads(value) for key, value in availability_data.items()}

    available_cards = []

    # Load user's wanted cards
    user_cards = load_card_list(username)

    for card in user_cards:
        card_name = card["card_name"]

        # Check if this card is available in any store
        stores_with_card = {
            store: listings
            for store, listings in parsed_data.items()
            if store.endswith(f"_{card_name}") and listings  # Ensure there are listings
        }

        if stores_with_card:
            available_cards.append({
                "card_name": card_name,
                "stores": stores_with_card
            })

    return available_cards  # Returns a list of available cards