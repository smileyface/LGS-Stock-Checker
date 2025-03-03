from utility.logger import logger
import os

import managers.database_manager as database_manager


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
    """Retrieves a user's selected stores."""
    return database_manager.get_user_stores(username)
