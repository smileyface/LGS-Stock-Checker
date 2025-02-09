import os
import json
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

def load_json(file_path):
    """Loads JSON data from a file."""
    logger.info(f"📥 Attempting to load JSON from: {file_path}")
    if not os.path.exists(file_path):
        logger.warning(f"🚨 File not found: {file_path}")
        return None
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except json.JSONDecodeError:
        logger.error(f"❌ Error: Could not decode JSON from {file_path}.")
        return None

def save_json(data, file_path):
    """Saves JSON data to a file."""
    logger.info(f"💾 Saving JSON to: {file_path}")
    try:
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)
    except Exception as e:
        logger.error(f"❌ Error: Could not save JSON to {file_path}. {e}")
    return True

def get_user_directory(username):
    """Returns the directory path for a user's data."""
    user_dir = os.path.join(USER_DATA_PATH, username)
    logger.info(f"📂 Resolving user directory: {user_dir}")
    os.makedirs(user_dir, exist_ok=True)  # Ensure user folder exists
    return user_dir

def load_users():
    """Loads all users from the `users.json` file."""
    logger.info("📥 Loading users...")
    return load_json(USER_DB_FILE) or {}

def save_users(users):
    """Saves all users to the `users.json` file."""
    logger.info("💾 Saving user database...")
    save_json(users, USER_DB_FILE)