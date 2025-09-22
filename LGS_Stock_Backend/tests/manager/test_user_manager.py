import pytest
from unittest.mock import MagicMock, call

from managers.user_manager import (
    get_user,
    add_user,
    update_username,
    authenticate_user,
    get_selected_stores,
    load_card_list,
    save_card_list,
)

# Base paths for patching dependencies as they are seen by each submodule.
USER_MANAGER_MODULE_PATH = "managers.user_manager.user_manager"
USER_AUTH_MODULE_PATH = "managers.user_manager.user_auth"
USER_CARDS_MODULE_PATH = "managers.user_manager.user_cards"
USER_PREFS_MODULE_PATH = "managers.user_manager.user_preferences"

# Paths for werkzeug security functions
GENERATE_HASH_PATH = f"{USER_MANAGER_MODULE_PATH}.generate_password_hash"
CHECK_HASH_PATH = f"{USER_AUTH_MODULE_PATH}.check_password_hash"

def test_get_user(mocker):
    """
    GIVEN a username
    WHEN get_user is called
    THEN it calls the data layer's get_user_for_display and returns the result.
    """
    # Arrange
    # Patch the 'database' object as it is seen by the user_manager.py module
    mock_database = mocker.patch(f"{USER_MANAGER_MODULE_PATH}.database")
    mock_user = MagicMock()
    mock_database.get_user_for_display.return_value = mock_user
    username = "testuser"

    # Act
    result = get_user(username)

    # Assert
    mock_database.get_user_for_display.assert_called_once_with(username)
    assert result is mock_user

def test_add_user(mocker):
    """
    GIVEN a new username and password
    WHEN add_user is called
    THEN it checks if the user exists, hashes the password, and calls the data layer to add the user.
    """
    # Arrange
    mock_database = mocker.patch(f"{USER_MANAGER_MODULE_PATH}.database")
    mock_user_exists = mocker.patch(f"{USER_MANAGER_MODULE_PATH}.user_exists", return_value=False)
    mock_hash_pw = mocker.patch(GENERATE_HASH_PATH, return_value="hashed_password")
    username = "newuser"
    password = "password123"

    # Act
    add_user(username, password)

    # Assert
    mock_user_exists.assert_called_once_with(username)
    mock_hash_pw.assert_called_once_with(password)
    mock_database.add_user.assert_called_once_with(username, "hashed_password")

def test_update_username(mocker):
    """
    GIVEN an old and new username for a successful update
    WHEN update_username is called
    THEN it checks for the existence of both users and calls the data layer to perform the update.
    """
    # Arrange
    mock_database = mocker.patch(f"{USER_MANAGER_MODULE_PATH}.database")
    # Mock user_exists to return False for the new name check, and True for the old name check.
    mock_user_exists = mocker.patch(
        f"{USER_MANAGER_MODULE_PATH}.user_exists", side_effect=[False, True]
    )
    old_username = "olduser"
    new_username = "newuser"

    # Act
    result = update_username(old_username, new_username)

    # Assert
    assert result is True
    expected_calls = [call(new_username), call(old_username)]
    mock_user_exists.assert_has_calls(expected_calls)
    mock_database.update_username.assert_called_once_with(old_username, new_username)

def test_authenticate_user_success(mocker):
    """
    GIVEN a user with a correct password
    WHEN authenticate_user is called
    THEN it retrieves the user ORM object and returns it after successful password check.
    """
    # Arrange
    mock_database = mocker.patch(f"{USER_AUTH_MODULE_PATH}.database")
    mock_user = MagicMock()
    mock_user.check_password.return_value = True
    mock_database.get_user_orm_by_username.return_value = mock_user

    # Act
    result = authenticate_user("testuser", "password123")

    # Assert
    mock_database.get_user_orm_by_username.assert_called_once_with("testuser")
    mock_user.check_password.assert_called_once_with("password123")
    assert result is mock_user

def test_authenticate_user_wrong_password(mocker):
    """
    GIVEN a user with an incorrect password
    WHEN authenticate_user is called
    THEN it retrieves the user, fails to verify the password, and returns None.
    """
    # Arrange
    mock_database = mocker.patch(f"{USER_AUTH_MODULE_PATH}.database")
    mock_user = MagicMock()
    mock_user.check_password.return_value = False
    mock_database.get_user_orm_by_username.return_value = mock_user

    # Act
    result = authenticate_user("testuser", "wrong_password")

    # Assert
    mock_database.get_user_orm_by_username.assert_called_once_with("testuser")
    mock_user.check_password.assert_called_once_with("wrong_password")
    assert result is None

def test_authenticate_user_no_user(mocker):
    """
    GIVEN a username that does not exist
    WHEN authenticate_user is called
    THEN it fails to retrieve a user and returns None without checking a password.
    """
    # Arrange
    mock_database = mocker.patch(f"{USER_AUTH_MODULE_PATH}.database")
    mock_database.get_user_orm_by_username.return_value = None

    # Act
    result = authenticate_user("nonexistent", "password")

    # Assert
    mock_database.get_user_orm_by_username.assert_called_once_with("nonexistent")

def test_get_selected_stores(mocker):
    """
    GIVEN a username
    WHEN get_selected_stores is called
    THEN it calls the data layer's get_user_stores and returns the result.
    """
    # Arrange
    mock_database = mocker.patch(f"{USER_PREFS_MODULE_PATH}.database")
    mock_stores = [MagicMock(), MagicMock()]
    mock_database.get_user_stores.return_value = mock_stores

    # Act
    result = get_selected_stores("testuser")

    # Assert
    mock_database.get_user_stores.assert_called_once_with("testuser")
    assert result is mock_stores

def test_load_card_list(mocker):
    """
    GIVEN a username for an existing user
    WHEN load_card_list is called
    THEN it checks if the user exists and calls the data layer to get the user's cards.
    """
    # Arrange
    mock_database = mocker.patch(f"{USER_CARDS_MODULE_PATH}.database")
    mock_database.get_user_by_username.return_value = True  # Simulate user exists
    mock_cards = [{"card_name": "test card"}]
    mock_database.get_users_cards.return_value = mock_cards

    # Act
    result = load_card_list("testuser")

    # Assert
    mock_database.get_user_by_username.assert_called_once_with("testuser")
    mock_database.get_users_cards.assert_called_once_with("testuser")
    assert result is mock_cards

def test_save_card_list(mocker):
    """
    GIVEN a username and a list of cards
    WHEN save_card_list is called
    THEN it checks if the user exists and calls the data layer to update the card list.
    """
    # Arrange
    mock_database = mocker.patch(f"{USER_CARDS_MODULE_PATH}.database")
    mock_database.get_user_by_username.return_value = True  # Simulate user exists
    card_list = [{"card_name": "test card", "amount": 1}]

    # Act
    save_card_list("testuser", card_list)

    # Assert
    mock_database.get_user_by_username.assert_called_once_with("testuser")
    mock_database.update_user_tracked_cards_list.assert_called_once_with("testuser", card_list)
