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


def get_user(username):
    """Retrieves a user's data, including selected stores."""
    logger.info(f"🔍 Fetching user data for: {username}")
    users = load_users()
    return users.get(username, {"selected_stores": []})

def get_all_users():
    """Returns a list of all registered usernames."""
    logger.info("📜 Fetching all users...")
    return list(load_users().keys())