import managers.database_manager as database_manager
from managers.user_manager.user_manager import user_exists
from utility.logger import logger


def load_card_list(username):
    """
    Loads a user's wanted card list from the database.

    Returns:
        list: A list of UserCardPreference objects if the user exists, otherwise an empty list.
    """
    if not user_exists(username):
        logger.warning(f"🚨 Attempted to load cards for non-existent user: '{username}'. Returning empty list.")
        return []

    logger.info(f"📖 Loading card list for user: '{username}'")
    cards = database_manager.get_users_cards(username)

    card_list = [
        {
            "card_name": card.card_name,
            "amount": card.amount,  # If applicable
            "card_specs": {
                "set_code": card.specifications.set_code if card.specifications else None,
                "collector_id": card.specifications.collector_id if card.specifications else None,
                "finish": card.specifications.finish if card.specifications else None
            }
        }
        for card in cards
    ]

    logger.info(f"✅ Loaded {len(card_list)} cards for user: '{username}'")
    return card_list


def save_card_list(username, card_list):
    """
    Saves a user's wanted card list into the database, replacing existing preferences.

    Args:
        username (str): The username of the user.
        card_list (list of dict): A list of card specifications to save.
                                  Each dictionary should have "card_name" and any optional set/finish filters.

    Returns:
        bool: True if successful, False if the user does not exist.
    """
    if not user_exists(username):
        logger.warning(f"🚨 Attempted to save cards for non-existent user: '{username}'")
        return False

    logger.info(f"💾 Saving card list for user: '{username}'")

    # Clear existing cards and add new ones
    database_manager.update_user_tracked_cards(username, card_list)

    logger.info(f"✅ Successfully saved {len(card_list)} cards for user: '{username}'")
    return True

