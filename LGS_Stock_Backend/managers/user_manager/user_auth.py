"""
User authentication functions for the application.

Includes functions to authenticate users and update their passwords.
"""

from werkzeug.security import check_password_hash, generate_password_hash

from data import database
from utility import logger


def authenticate_user(username: str, password: str) -> bool:
    """
    Authenticate a user by username and password.
    Args:
        username (str): The username of the user to authenticate.
        password (str): The password to authenticate the user.

    Returns:
        bool: True if the user is authenticated, False otherwise.

    Logs:
        Success or failure of the authentication operation.
    """
    logger.info(f"🔑 Authenticating user: {username}")

    user_data = database.get_user_by_username(username)

    if not user_data:
        logger.warning(f"❌ User '{username}' not found.")
        return False

    if check_password_hash(user_data.password_hash, password):
        logger.info(f"✅ User '{username}' authenticated.")
        return True

    logger.warning(f"❌ Authentication failed for user: {username}")
    return False


def update_password(username: str, old_password: str, new_password: str) -> bool:
    """
    Update the password for a user identified by username.

    Args:
        username (str): The username of the user whose password is to be updated.
        old_password (str): The current hashed password.
        new_password (str): The new hashed password.

    Returns:
        bool: True if the password update was successful, False otherwise.

    Logs:
        Success or failure of the password update operation.
    """
    logger.info(f"🔑 Updating password for user: {username}")
    user_data = database.get_user_by_username(username)
    if not user_data or not check_password_hash(user_data.password_hash, old_password):
        logger.warning(f"❌ Password update failed for {username}. Incorrect current password.")
        return False

    new_password_hash = generate_password_hash(new_password)
    database.update_password(username, new_password_hash)
    logger.info(f"✅ Password for user '{username}' updated successfully!")
    return True
