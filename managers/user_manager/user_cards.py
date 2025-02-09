from managers.user_manager.user_storage import get_user_directory, load_json, save_json
from utility.logger import logger
import os


def load_card_list(username):
    """Loads a user's wanted card list."""
    logger.info(f"📖 Loading card list for user '{username}'")
    return load_json(os.path.join(get_user_directory(username), "card_list.json")) or []


def save_card_list(username, card_list):
    """Saves a user's wanted card list."""
    logger.info(f"💾 Saving card list for user '{username}'")
    save_json(card_list, os.path.join(get_user_directory(username), "card_list.json"))
