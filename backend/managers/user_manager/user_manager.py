from typing import Optional

from werkzeug.security import generate_password_hash

from data import database
from schema import db
from utility import logger


def get_public_user_profile(
    username: str,
) -> Optional[db.UserPublicSchema]:
    """
    Retrieve a user's public profile by username, excluding sensitive fields,
      and return as a UserPublicSchema instance.
    Args:
        username (str): The unique username of the user to fetch.

    Returns:
        Optional[db.UserPublicSchema]: The user data as a
        UserPublicSchema if found, otherwise None.
    """
    return database.get_user_for_display(username)


def user_exists(username: str) -> bool:
    """
    Checks if a user already exists in the database.
    Args:
        username (str): The username to check.
    Returns:
        bool: True if the user exists, False otherwise.
    """
    return database.get_user_by_username(username) is not None


def add_user(username: str, password: str) -> bool:
    """Creates a new user with a hashed password."""
    logger.info(f"➕ Adding user: {username}")

    if not password or not isinstance(password, str):
        logger.error(
            f"❌ Attempted to add user '{username}' with an invalid password."
        )
        return False

    # Check if user already exists
    if user_exists(username):
        logger.warning(f"🚨 User '{username}' already exists.")
        return False

    hashed_password = generate_password_hash(
        password
    )  # ✅ Hash password BEFORE inserting
    result = database.add_user(username, hashed_password)

    if result:
        logger.info(f"✅ User '{username}' added successfully.")
        return True
    else:
        logger.error(f"❌ Failed to add user '{username}' at the data layer.")
        return False


def update_username(old_username: str, new_username: str) -> bool:
    """
    Renames a user's account, transferring all associated data.
    Args:
        old_username (str): The current username of the user to be renamed.
        new_username (str): The new desired username for the user.
    Returns:
        bool: True if the update was successful, False otherwise.
    Logs:
        Success or failure of the username update operation.
    """
    logger.info(f"✏️ Renaming user '{old_username}' to '{new_username}'")
    if user_exists(new_username):
        logger.warning(f"🚨 User '{new_username}' already exists.")
        return False
    if user_exists(old_username):
        database.update_username(old_username, new_username)
        logger.info("✅ Username updated successfully.")
        return True
    else:
        logger.warning(f"🚨 User '{old_username}' not found. Cannot rename.")
        return False
