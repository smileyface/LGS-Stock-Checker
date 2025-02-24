from managers.user_manager.user_manager import get_user
from managers.user_manager.user_storage import get_user_directory, save_users, load_users, load_json, save_json
from utility.logger import logger
import os


def update_selected_stores(username, selected_stores):
    """Updates a user's preferred stores."""
    logger.info(f"🛍️ Updating stores for user '{username}': {selected_stores}")
    users = load_users()
    if username in users:
        users[username]["selected_stores"] = selected_stores
        save_users(users)
    else:
        logger.warning(f"🚨 User '{username}' not found.")


def get_selected_stores(username):
    """Returns the selected stores for a given user."""
    users = get_user("all")  # Fetch all users
    logger.info(f"🔍 Users data type: {type(users)} | Content: {users}")  # Debug log

    if isinstance(users, list):
        # If users is a list of dicts, find the right one
        user_data = next((u for u in users if u.get("username") == username), None)
        if user_data:
            return user_data.get("selected_stores", [])
        return []  # Default empty if user not found

    # If users is a dictionary, continue as expected
    return users.get(username, {}).get("selected_stores", [])



def load_user_config(username):
    """Loads a user's settings (e.g., selected stores)."""
    logger.info(f"⚙️ Loading config for user '{username}'")
    return load_json(os.path.join(get_user_directory(username), "config.json")) or {}


def save_user_config(username, config_data):
    """Saves a user's settings (e.g., selected stores)."""
    logger.info(f"💾 Saving config for user '{username}'")
    save_json(config_data, os.path.join(get_user_directory(username), "config.json"))
