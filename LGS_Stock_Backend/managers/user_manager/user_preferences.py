from typing import List

from data import database
from utility import logger


def update_selected_stores(username: str, selected_stores: List[str]):
    """Updates a user's preferred stores."""
    logger.info(f"🛍️ Updating stores for user '{username}': {selected_stores}")

    if not selected_stores:
        logger.info(f"No stores provided for '{username}'. No update needed.")
        return True

    # Fetch user's current store preferences
    current_stores = get_selected_stores(username)

    if current_stores is None:
        logger.error(f"❌ Failed to retrieve stores for '{username}'")
        return False

    # Convert to a set of slugs for efficient lookup
    current_store_slugs = {store.slug for store in current_stores}

    # Add only new stores (prevent duplicates)
    for store_slug in selected_stores:
        if store_slug not in current_store_slugs:
            database.add_user_store(username, store_slug)
            logger.info(f"✅ Added store '{store_slug}' for user '{username}'.")

    logger.info(f"🎯 Store preferences updated for '{username}'.")
    return True


def get_selected_stores(username):
    """Retrieves a user's selected stores."""
    return database.get_user_stores(username)
