from typing import Optional
from werkzeug.security import check_password_hash, generate_password_hash

import managers.database_manager as database_manager
from utility.logger import logger


def authenticate_user(username: str, password: str) -> bool:
    """
    Authenticate a user by verifying the provided password against the stored hash.
    
    Args:
        username (str): The username of the user to authenticate.
        password (str): The password provided by the user.
    
    Returns:
        bool: True if authentication is successful, False otherwise.
    """
    logger.info(f"🔑 Authenticating user: {username}")

    user = database_manager.get_user_by_username(username)
    if not user:
        logger.warning(f"❌ User '{username}' not found.")
        return False

    if check_password_hash(user.password_hash, password):
        logger.info(f"✅ User '{username}' authenticated.")
        return True

    logger.warning(f"❌ Authentication failed for user: {username}")
    return False


def update_password(username: str, old_password: str, new_password: str) -> bool:
    """
    Update a user's password after verifying the current password.
    
    Args:
        username (str): The username of the user whose password is to be updated.
        old_password (str): The current password of the user.
        new_password (str): The new password to set for the user.
    
    Returns:
        bool: True if the password is successfully updated, False otherwise.
    """
    if not authenticate_user(username, old_password):
        logger.warning(f"❌ Password update failed for {username}. Incorrect current password.")
        return False

    hashed_password = generate_password_hash(new_password)
    database_manager.update_password(username, hashed_password)
    logger.info(f"✅ Password updated successfully for {username}.")
    return True
