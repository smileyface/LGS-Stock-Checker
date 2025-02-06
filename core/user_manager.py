import os
import sys
import json
from werkzeug.security import check_password_hash, generate_password_hash

def log(message):
    print(message)
    sys.stdout.flush()  # Forces immediate log output in Docker

# 🔹 File Paths
BASE_DIR = "/data"
USER_DATA_PATH = os.path.join(BASE_DIR, "user_data")
USER_DB_FILE = os.path.join(BASE_DIR, "users.json")

log(f"📁 BASE_DIR: {BASE_DIR}")
log(f"📁 USER_DATA_PATH: {USER_DATA_PATH}")
log(f"📁 USER_DB_FILE: {USER_DB_FILE}")

if os.path.exists(USER_DB_FILE) and not os.path.isfile(USER_DB_FILE):
    print(f"❌ ERROR: `{USER_DB_FILE}` is a directory! Fixing it now...")

# Ensure directories exist
log(f"🔧 Ensuring user data directory exists at: {USER_DATA_PATH}")
os.makedirs(USER_DATA_PATH, exist_ok=True)


### 🔹 Utility Functions ###
def load_json(file_path):
    """Loads JSON data from a file."""
    log(f"📥 Attempting to load JSON from: {file_path}")
    if not os.path.exists(file_path):
        log(f"🚨 File not found: {file_path}")
        return None
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except json.JSONDecodeError:
        log(f"❌ Error: Could not decode JSON from {file_path}.")
        return None


def save_json(data, file_path):
    """Saves JSON data to a file."""
    log(f"💾 Saving JSON to: {file_path}")
    try:
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)
    except Exception as e:
        log(f"❌ Error: Could not save JSON to {file_path}. {e}")


def get_user_directory(username):
    """Returns the directory path for a user's data."""
    user_dir = os.path.join(USER_DATA_PATH, username)
    log(f"📂 Resolving user directory: {user_dir}")
    os.makedirs(user_dir, exist_ok=True)  # Ensure user folder exists
    return user_dir


### 🔹 User Account Management ###
def load_users():
    """Loads all users from the `users.json` file."""
    log("📥 Loading users...")
    return load_json(USER_DB_FILE) or {}


def save_users(users):
    """Saves all users to the `users.json` file."""
    log("💾 Saving user database...")
    save_json(users, USER_DB_FILE)


def get_user(username):
    """Retrieves a user's data, including selected stores."""
    log(f"🔍 Fetching user data for: {username}")
    users = load_users()
    return users.get(username, {"selected_stores": []})


def add_user(username, password):
    """Creates a new user with a hashed password."""
    log(f"➕ Adding user: {username}")
    users = load_users()
    if username in users:
        log(f"🚨 User '{username}' already exists.")
        return False

    hashed_password = generate_password_hash(password)
    users[username] = {"password": hashed_password, "selected_stores": []}
    save_users(users)
    log(f"✅ User '{username}' added successfully.")
    return True


def authenticate_user(username, password):
    """Checks if the provided password matches the stored hash."""
    log(f"🔑 Authenticating user: {username}")
    users = load_users()
    if username in users:
        return check_password_hash(users[username]["password"], password)
    log(f"❌ Authentication failed for user: {username}")
    return False


def update_username(old_username, new_username):
    """Renames a user's account, transferring all associated data."""
    log(f"✏️ Renaming user '{old_username}' to '{new_username}'")
    users = load_users()
    if old_username in users:
        users[new_username] = users.pop(old_username)
        os.rename(get_user_directory(old_username), get_user_directory(new_username))
        save_users(users)
        log(f"✅ Username updated successfully.")
    else:
        log(f"🚨 User '{old_username}' not found.")


def update_selected_stores(username, selected_stores):
    """Updates a user's preferred stores."""
    log(f"🛍️ Updating stores for user '{username}': {selected_stores}")
    users = load_users()
    if username in users:
        users[username]["selected_stores"] = selected_stores
        save_users(users)
    else:
        log(f"🚨 User '{username}' not found.")


def get_all_users():
    """Returns a list of all registered usernames."""
    log("📜 Fetching all users...")
    return list(load_users().keys())


### 🔹 User Preferences (Config) ###
def load_user_config(username):
    """Loads a user's settings (e.g., selected stores)."""
    log(f"⚙️ Loading config for user '{username}'")
    return load_json(os.path.join(get_user_directory(username), "config.json")) or {}


def save_user_config(username, config_data):
    """Saves a user's settings (e.g., selected stores)."""
    log(f"💾 Saving config for user '{username}'")
    save_json(config_data, os.path.join(get_user_directory(username), "config.json"))


### 🔹 Card List Management ###
def load_card_list(username):
    """Loads a user's wanted card list."""
    log(f"📖 Loading card list for user '{username}'")
    return load_json(os.path.join(get_user_directory(username), "card_list.json")) or []


def save_card_list(username, card_list):
    """Saves a user's wanted card list."""
    log(f"💾 Saving card list for user '{username}'")
    save_json(card_list, os.path.join(get_user_directory(username), "card_list.json"))


def get_selected_stores(username):
    users = load_users()
    return users.get(username, {}).get("selected_stores", [])
