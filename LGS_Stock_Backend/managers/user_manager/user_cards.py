from typing import List, Dict

from data import database
from utility import logger


def load_card_list(username):
    """
    Loads a user's wanted card list from the database.

    Returns:
        list: A list of UserCardPreference objects if the user exists, otherwise an empty list.
    """
    if not database.get_user_by_username(username):
        logger.warning(f"🚨 Attempted to load cards for non-existent user: '{username}'. Returning empty list.")
        return []

    logger.info(f"📖 Loading card list for user: '{username}'")
    cards = database.get_users_cards(username)

    logger.info(f"✅ Loaded {len(cards)} cards for user: '{username}'")
    return cards


def save_card_list(username: str, card_list: List[Dict]):
    """
    Saves a user's wanted card list into the database, replacing existing preferences.

    Args:
        username (str): The username of the user.
        card_list (list of dict): A list of card specifications to save.
                                  Each dictionary should have "card_name" and any optional set/finish filters.

    Returns:
        bool: True if successful, False if the user does not exist.
    """
    if not database.get_user_by_username(username):
        logger.warning(f"🚨 Attempted to save cards for non-existent user: '{username}'")
        return False

    logger.info(f"💾 Saving card list for user: '{username}'")

    # Clear existing cards and add new ones
    database.update_user_tracked_cards_list(username, card_list)

    logger.info(f"✅ Successfully saved {len(card_list)} cards for user: '{username}'")
    return True
