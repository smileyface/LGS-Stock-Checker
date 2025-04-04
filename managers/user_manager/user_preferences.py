from typing import List
import managers.database_manager as database_manager
from utility.logger import logger


def update_selected_stores(username: str, selected_stores: list) -> bool:
    """
    Update a user's preferred stores with a new selection.

    Logs the update process and ensures no duplicate stores are added
    to the user's preferences. Returns True if the update is successful,
    otherwise logs an error and returns False.

    Args:
        username (str): The username of the user whose store preferences are to be updated.
        selected_stores (list): A list of store slugs to be added to the user's preferences.

    Returns:
        bool: True if the update is successful, False otherwise.
    """
    logger.info(f"🛍️ Updating stores for user '{username}': {selected_stores}")

    # Fetch user's current store preferences
    current_stores = get_selected_stores(username)

    if current_stores is None:
        logger.error(f"❌ Failed to retrieve stores for '{username}'")
        return False

    # Convert to set for faster lookup
    current_store_set = set(current_stores)

    # Add only new stores (prevent duplicates)
    new_stores = set(selected_stores) - current_store_set
    for store in new_stores:
        database_manager.add_user_store(username, store)
        logger.info(f"✅ Added store '{store}' for user '{username}'.")

    logger.info(f"🎯 Store preferences updated for '{username}'.")
    return True


def get_selected_stores(username: str) -> List[str]:
    """
    Retrieve the list of stores selected by a specific user.

    Args:
        username (str): The username of the user whose selected stores are to be retrieved.

    Returns:
        list: A list of store objects associated with the user.
    """
    return database_manager.get_user_stores(username)
