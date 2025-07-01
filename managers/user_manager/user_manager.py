from typing import Optional

from werkzeug.security import generate_password_hash

import data
from data.database import schema
from utility.logger import logger


def get_user(username: str) -> Optional[schema.UserPublicSchema]:
    """
    Retrieve a user by username from the database, excluding sensitive fields, and return as a UserPublicSchema instance.

    Args:
        username (str): The unique username of the user to fetch.
        session: The database session, injected by the db_query decorator.

    Returns:
        UserPublicSchema or None: The user data as a UserPublicSchema if found, otherwise None.
    """
    return data.get_user_for_display(username)


def user_exists(username):
    """
    Checks if a user already exists in the database.
    Returns True if exists, False otherwise.
    """
    return data.get_user_by_username(username) is not None


def add_user(username: str, password: str) -> bool:
    """Creates a new user with a hashed password."""
    logger.info(f"➕ Adding user: {username}")

    if not password or not isinstance(password, str):
        logger.error(f"❌ Attempted to add user '{username}' with an invalid password.")
        return False

    # Check if user already exists
    if user_exists(username):
        logger.warning(f"🚨 User '{username}' already exists.")
        return False

    hashed_password = generate_password_hash(password)  # ✅ Hash password BEFORE inserting
    data.add_user(username, hashed_password)

    logger.info(f"✅ User '{username}' added successfully.")
    return True


def update_username(old_username, new_username):
    """Renames a user's account, transferring all associated data."""
    logger.info(f"✏️ Renaming user '{old_username}' to '{new_username}'")
    if user_exists(old_username):
        data.update_username(old_username, new_username)
        logger.info(f"✅ Username updated successfully.")
    else:
        logger.warning(f"🚨 User '{old_username}' not found.")
