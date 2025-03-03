from werkzeug.security import generate_password_hash

import managers.database_manager as database_manager
from utility.logger import logger


def get_user(username):
    """
    Fetch user details by username.
    Returns a dictionary containing user details or None if not found.
    """
    user = database_manager.get_user_by_username(username)
    if user:
        return {
            "username": user.username,
            "password_hash": user.password_hash,
            "selected_stores": user.selected_stores  # Assuming JSON serialized list
        }
    return None


def user_exists(username):
    """
    Checks if a user already exists in the database.
    Returns True if exists, False otherwise.
    """
    return database_manager.get_user_by_username(username) is not None


def add_user(username, password):
    """Creates a new user with a hashed password."""
    logger.info(f"➕ Adding user: {username}")

    # Check if user already exists
    if user_exists(username):
        logger.warning(f"🚨 User '{username}' already exists.")
        return False

    hashed_password = generate_password_hash(password)  # ✅ Hash password BEFORE inserting
    database_manager.add_user(username, hashed_password)

    logger.info(f"✅ User '{username}' added successfully.")
    return True


def update_username(old_username, new_username):
    """Renames a user's account, transferring all associated data."""
    logger.info(f"✏️ Renaming user '{old_username}' to '{new_username}'")
    if user_exists(old_username):
        database_manager.update_username(old_username, new_username)
        logger.info(f"✅ Username updated successfully.")
    else:
        logger.warning(f"🚨 User '{old_username}' not found.")
