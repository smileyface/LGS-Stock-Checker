import data.database as db
from utility.logger import logger


def update_selected_stores(username, selected_stores):
    """Updates a user's preferred stores."""
    logger.info(f"🛍️ Updating stores for user '{username}': {selected_stores}")

    # Fetch user's current store preferences
    current_stores = get_selected_stores(username)

    if current_stores is None:
        logger.error(f"❌ Failed to retrieve stores for '{username}'")
        return False

    # Convert to set for faster lookup
    current_store_set = set(current_stores)

    # Add only new stores (prevent duplicates)
    for store in selected_stores:
        if store not in current_store_set:
            db.add_user_store(username, store)
            logger.info(f"✅ Added store '{store}' for user '{username}'.")

    logger.info(f"🎯 Store preferences updated for '{username}'.")
    return True


def get_selected_stores(username):
    """Retrieves a user's selected stores."""
    return db.get_user_stores(username)
