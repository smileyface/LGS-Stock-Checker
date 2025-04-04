from typing import Optional, Dict, Any
from werkzeug.security import generate_password_hash

import managers.database_manager as database_manager
from utility.logger import logger


def get_user(username: str) -> Optional[Dict[str, Any]]:
    """
    Fetch user details by username.

    Args:
        username (str): The username of the user to fetch.

    Returns:
        dict or None: A dictionary containing user details such as username,
        password hash, and selected stores if the user is found; otherwise, None.
    """
    user = database_manager.get_user_by_username(username)
    if not user:
        return None

    return {
        "username": user.username,
        "password_hash": user.password_hash,
        "selected_stores": database_manager.get_user_stores(username)  # Assuming JSON serialized list
    }


def user_exists(username: str) -> bool:
    """
    Check if a user exists in the database.

    Args:
        username (str): The username to check for existence.

    Returns:
        bool: True if the user exists, False otherwise.
    """
    return bool(database_manager.get_user_by_username(username))


"""
Adds a new user to the database with a hashed password.

Logs the process of adding a user, checks for existing users,
and returns a boolean indicating success or failure.

Args:
    username (str): The username of the new user.
    password (str): The plaintext password of the new user.

Returns:
    bool: True if the user was added successfully, False if the user already exists.
"""


def add_user(username: str, password: str) -> bool:
    """
    Adds a new user to the database with a hashed password.

    Logs the process of adding a user, checks for existing users,
    and returns a boolean indicating success or failure.

    Args:
        username (str): The username of the new user.
        password (str): The plaintext password of the new user.

    Returns:
        bool: True if the user was added successfully, False if the user already exists.
    """
    logger.info(f"➕ Adding user: {username}")

    if user_exists(username):
        logger.warning(f"🚨 User '{username}' already exists.")
        return False

    hashed_password = generate_password_hash(password)
    database_manager.add_user(username, hashed_password)

    logger.info(f"✅ User '{username}' added successfully.")
    return True


def update_username(old_username: str, new_username: str) -> None:
    """
    Renames a user's account by updating the username in the database.

    Logs the renaming process and checks if the user exists before attempting
    the update. If the user does not exist, logs a warning message.

    Args:
        old_username (str): The current username of the user.
        new_username (str): The new username to assign to the user.
    """
    logger.info(f"✏️ Renaming user '{old_username}' to '{new_username}'")

    if not user_exists(old_username):
        logger.warning(f"🚨 User '{old_username}' not found.")
        return

    database_manager.update_username(old_username, new_username)
    logger.info("✅ Username updated successfully.")
