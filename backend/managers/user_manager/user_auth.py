"""
User authentication functions for the application.

Includes functions to authenticate users and update their passwords.
"""

from typing import Optional

from werkzeug.security import check_password_hash, generate_password_hash

from data import database
from data.database.schema.user_schema import UserDBSchema
from data.database.models.orm_models import User
from utility import logger


def authenticate_user(username: str, password: str) -> Optional[User]:
    """
    Authenticate a user by username and password.

    Args:
        username (str): The username of the user to authenticate.
        password (str): The password to authenticate the user.

    Returns:
        User or None: The user ORM object if authenticated, otherwise None.
    """
    logger.info(f"🔑 Authenticating user: {username}")

    # Fetch the full ORM object, which includes the password hash and methods.
    user_orm = database.get_user_orm_by_username(username)

    if not user_orm:
        logger.warning(f"❌ User '{username}' not found.")
        return None

    if check_password_hash(user_orm.password_hash, password):
        logger.info(f"✅ User '{username}' authenticated.")
        return user_orm

    logger.warning(f"❌ Authentication failed for user: {username}")
    return None  # Return None on password failure


def update_password(
    username: str, old_password: str, new_password: str
) -> bool:
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
    if not user_data or not check_password_hash(
        user_data.password_hash, old_password
    ):
        logger.warning(
            f"❌ Password update failed for {username}. Incorrect current password."
        )
        return False

    new_password_hash = generate_password_hash(new_password)
    database.update_password(username, new_password_hash)
    logger.info(f"✅ Password for user '{username}' updated successfully!")
    return True


def load_user_by_id(user_id: str) -> User:
    """
    Load a user from the database by their ID.
    This function is used by Flask-Login's user_loader.

    Args:
        user_id (str): The ID of the user to load.

    Returns:
        User: The user object if found, otherwise None.
    """
    # The user_id from the session is a string, so it must be cast to an integer.
    # This now correctly uses the repository layer.
    return database.get_user_orm_by_id(int(user_id))
