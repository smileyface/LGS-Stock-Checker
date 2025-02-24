import os
from managers.user_manager import get_user_directory, load_json, save_json


def load_card_list(username):
    """Loads the card list for a user."""
    return load_json(os.path.join(get_user_directory(username), "card_list.json")) or []


def save_card_list(username, card_list):
    """Saves the card list for a user."""
    save_json(card_list, os.path.join(get_user_directory(username), "card_list.json"))
