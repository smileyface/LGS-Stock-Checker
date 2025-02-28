import os

from werkzeug.security import check_password_hash, generate_password_hash

import managers.database_manager as database_manager
from utility.logger import logger



def authenticate_user(username, password):
    """Checks if the provided password matches the stored hash."""
    logger.info(f"🔑 Authenticating user: {username}")

    user = database_manager.get_user_by_username(username)

    if check_password_hash(user.password, password):
        logger.info(f"✅ User '{username}' authenticated.")
        return True
    logger.warning(f"❌ Authentication failed for user: {username}")
    return False


def update_password(username, old_password, new_password):
    """Updates a user's password after verifying the old one."""
    if not authenticate_user(username, old_password):  # ❌ Reject if authentication fails
        logger.warning(f"❌ Password update failed for {username}. Incorrect current password.")
        return False

    database_manager.update_password(username, generate_password_hash(new_password))
    logger.info(f"✅ Password updated successfully for {username}.")
    return True