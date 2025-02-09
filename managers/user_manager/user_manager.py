import os
import sys
import json
from werkzeug.security import check_password_hash, generate_password_hash
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
from managers.user_manager.user_storage import load_json, save_json, get_user_directory

# 🔹 User Account Management
from managers.user_manager.user_auth import add_user, authenticate_user, update_username

# 🔹 User Preferences
from managers.user_manager.user_preferences import update_selected_stores, get_selected_stores, load_user_config, save_user_config

# 🔹 Card List Management
from managers.user_manager.user_cards import load_card_list, save_card_list

# 🔹 User Data Management
def load_users():
    """Loads all users from the `users.json` file."""
    logger.info("📥 Loading users...")
    return load_json(USER_DB_FILE) or {}

def save_users(users):
    """Saves all users to the `users.json` file."""
    logger.info("💾 Saving user database...")
    save_json(users, USER_DB_FILE)

def get_user(username):
    """Retrieves a user's data, including selected stores."""
    logger.info(f"🔍 Fetching user data for: {username}")
    users = load_users()
    return users.get(username, {"selected_stores": []})

def get_all_users():
    """Returns a list of all registered usernames."""
    logger.info("📜 Fetching all users...")
    return list(load_users().keys())