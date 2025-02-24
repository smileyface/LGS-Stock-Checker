import os

from utility.logger import logger

# 🔹 File Paths
BASE_DIR = "/data"
USER_DATA_PATH = os.path.join(BASE_DIR, "user_data")
USER_DB_FILE = os.path.join(BASE_DIR, "users.json")

logger.info(f"📁 BASE_DIR: {BASE_DIR}")
logger.info(f"📁 USER_DATA_PATH: {USER_DATA_PATH}")
logger.info(f"📁 USER_DB_FILE: {USER_DB_FILE}")

# Ensure directories exist
logger.info(f"🔧 Ensuring user data directory exists at: {USER_DATA_PATH}")
os.makedirs(USER_DATA_PATH, exist_ok=True)

# 🔹 Utility Functions
from managers.user_manager.user_storage import load_users


# 🔹 User Account Management

# 🔹 User Preferences

# 🔹 Card List Management

# 🔹 User Data Management


def get_user(mode):
    """Fetches user data."""
    users_data = load_users()

    if mode == "all":
        # Convert list to dict if necessary
        if isinstance(users_data, list):
            return {user["username"]: user for user in users_data if "username" in user}
        return users_data  # Already a dictionary

    return users_data.get(mode)  # Return specific user

def get_all_users():
    """Returns a list of all registered usernames."""
    logger.info("📜 Fetching all users...")
    return list(load_users().keys())