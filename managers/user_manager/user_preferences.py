from managers.user_manager.user_storage import get_user_directory, load_json, save_json
from utility.logger import logger
import os


def update_selected_stores(username, selected_stores):
    """Updates a user's preferred stores."""
    logger.info(f"🛍️ Updating stores for user '{username}': {selected_stores}")
    users = load_json(get_user_directory(username))
    if username in users:
        users[username]["selected_stores"] = selected_stores
        save_json(users)
    else:
        logger.warning(f"🚨 User '{username}' not found.")


def get_selected_stores(username):
    """Retrieves a user's selected stores."""
    users = load_json(get_user_directory(username))
    return users.get(username, {}).get("selected_stores", [])


def load_user_config(username):
    """Loads a user's settings (e.g., selected stores)."""
    logger.info(f"⚙️ Loading config for user '{username}'")
    return load_json(os.path.join(get_user_directory(username), "config.json")) or {}


def save_user_config(username, config_data):
    """Saves a user's settings (e.g., selected stores)."""
    logger.info(f"💾 Saving config for user '{username}'")
    save_json(config_data, os.path.join(get_user_directory(username), "config.json"))
