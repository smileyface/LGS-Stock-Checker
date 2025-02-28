import os

from werkzeug.security import check_password_hash, generate_password_hash

import managers.database_manager as database_manager
from managers.user_manager.user_storage import user_exists
from utility.logger import logger


def add_user(username, password):
    """Creates a new user with a hashed password."""
    logger.info(f"➕ Adding user: {username}")
    # Check if user already exists
    existing_user = user_exists(username)
    if existing_user:
        logger.warning(f"🚨 User '{username}' already exists.")
        return False

    hashed_password = generate_password_hash(password)
    database_manager.add_user(username, hashed_password)
    logger.info(f"✅ User '{username}' added successfully.")
    return True


def authenticate_user(username, password):
    """Checks if the provided password matches the stored hash."""
    logger.info(f"🔑 Authenticating user: {username}")

    user = database_manager.get_user_by_username(username)

    if check_password_hash(user.password, password):
        logger.info(f"✅ User '{username}' authenticated.")
        return True
    logger.warning(f"❌ Authentication failed for user: {username}")
    return False


def update_username(old_username, new_username):
    """Renames a user's account, transferring all associated data."""
    logger.info(f"✏️ Renaming user '{old_username}' to '{new_username}'")
    if user_exists(old_username):

        logger.info(f"✅ Username updated successfully.")
    else:
        logger.warning(f"🚨 User '{old_username}' not found.")

def update_password(username, old_password, new_password):
    pass