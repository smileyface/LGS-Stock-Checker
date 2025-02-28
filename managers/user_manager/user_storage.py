
import managers.database_manager as database_manager

def get_user(username):
    """
    Fetch user details by username.
    Returns a dictionary containing user details or None if not found.
    """
    user = database_manager.get_user_by_username(username)
    if user:
        return {
            "username": user.username,
            "password_hash": user.password_hash,
            "selected_stores": user.selected_stores  # Assuming JSON serialized list
        }
    return None

def add_new_user(username, password_hash):
    """
    Adds a new user to the database.
    Returns the created user object.
    """
    return database_manager.add_user_to_db(username, password_hash)

def user_exists(username):
    """
    Checks if a user already exists in the database.
    Returns True if exists, False otherwise.
    """
    return database_manager.get_user_by_username(username) is not None
