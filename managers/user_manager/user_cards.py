from typing import List, Dict
import managers.database_manager as database_manager
from managers.user_manager.user_manager import user_exists
from utility.logger import logger


def load_card_list(username: str) -> List[Dict]:
    """
    Loads a user's desired card list from the database.

    Args:
        username (str): The username of the user whose card list is to be loaded.

    Returns:
        list: A list of dictionaries representing the user's card preferences,
        each containing card details and specifications. Returns an empty list
        if the user does not exist.
    """
    """Retrieve and format a list of cards for a given username."""
    if not user_exists(username):
        logger.warning(f"🚨 Attempted to load cards for non-existent user: '{username}'. Returning empty list.")
        return []

    logger.info(f"📖 Loading card list for user: '{username}'")
    cards = database_manager.get_users_cards(username)

    card_list = [
        {
            "card_name": card.card_name,
            "amount": card.amount,
            "specifications": [
                {"set_code": spec.set_code, "collector_number": spec.collector_number, "finish": spec.finish}
                for spec in card.specifications or []
            ],
        }
        for card in cards
    ]

    logger.info(f"✅ Loaded {len(card_list)} cards for user: '{username}'")
    return card_list


def save_card_list(username: str, card_list: list[dict]) -> bool:
    """
    Save a list of card preferences for a user.

    Args:
        username (str): The username of the user.
        card_list (list of dict): A list of card preferences to save.

    Returns:
        bool: True if the card list was successfully saved, False if the user does not exist.
    """
    if not user_exists(username):
        logger.warning(f"🚨 Attempted to save cards for non-existent user: '{username}'")
        return False

    logger.info(f"💾 Saving card list for user: '{username}'")

    # Clear existing cards and add new ones
    database_manager.update_user_tracked_cards_list(username, card_list)

    logger.info(f"✅ Successfully saved {len(card_list)} cards for user: '{username}'")
    return True

