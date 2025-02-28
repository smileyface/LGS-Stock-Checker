from utility.logger import logger
import os


def load_card_list(username):
    """Loads a user's wanted card list."""
    logger.info(f"📖 Loading card list for user '{username}'")
    card_list = load_json(os.path.join(get_user_directory(username), "card_list.json")) or []
    logger.info(f"📖 Card list returned size {len(card_list)}")
    return card_list


def save_card_list(username, card_list):
    """Saves a user's wanted card list."""
    logger.info(f"💾 Saving card list for user '{username}'")
    save_json(card_list, os.path.join(get_user_directory(username), "card_list.json"))
