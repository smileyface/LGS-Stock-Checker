import os

from werkzeug.security import check_password_hash, generate_password_hash

from managers.user_manager.user_storage import load_users, save_users, get_user_directory
from utility.logger import logger


def add_user(username, password):
    """Creates a new user with a hashed password."""
    logger.info(f"➕ Adding user: {username}")
    users = load_users()
    if users is None:
        users = {}
    if username in users:
        logger.warning(f"🚨 User '{username}' already exists.")
        return False

    hashed_password = generate_password_hash(password)
    users[username] = {"password": hashed_password, "selected_stores": []}
    save_users(users)
    logger.info(f"✅ User '{username}' added successfully.")
    return True


def authenticate_user(username, password):
    """Checks if the provided password matches the stored hash."""
    logger.info(f"🔑 Authenticating user: {username}")
    if not os.path.exists(get_user_directory("users.json")):
        logger.warning("🚨 users.json not found. Creating a new empty user database.")
        save_users({})  # Create an empty users.json file
        return None

    users = load_users()

    if username in users:
        return check_password_hash(users[username]["password"], password)
    logger.warning(f"❌ Authentication failed for user: {username}")
    return None


def update_username(old_username, new_username):
    """Renames a user's account, transferring all associated data."""
    logger.info(f"✏️ Renaming user '{old_username}' to '{new_username}'")
    users = load_users()
    if old_username in users:
        users[new_username] = users.pop(old_username)
        os.rename(get_user_directory(old_username), get_user_directory(new_username))
        save_users(users)
        logger.info(f"✅ Username updated successfully.")
    else:
        logger.warning(f"🚨 User '{old_username}' not found.")


def update_password(username, old_password, new_password):
    users = load_users()
    if authenticate_user(username, old_password):
        users[username]["password"] = generate_password_hash(new_password)
