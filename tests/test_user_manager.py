import pytest
from unittest.mock import MagicMock

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
    Unit test for get_user.
    Verifies it calls the data layer and returns the result.
    """
    # Arrange
    # Patch the 'data' object as it is seen by the user_manager.py module
    mock_data = mocker.patch(f"{USER_MANAGER_MODULE_PATH}.data")
    mock_user = MagicMock()
    mock_data.get_user_for_display.return_value = mock_user
    username = "testuser"

    # Act
    result = get_user(username)

    # Assert
    mock_data.get_user_for_display.assert_called_once_with(username)
    assert result is mock_user

def test_add_user(mocker):
    """
    Unit test for add_user.
    Verifies it hashes the password and calls the data layer.
    """
    # Arrange
    mock_data = mocker.patch(f"{USER_MANAGER_MODULE_PATH}.data")
    mock_user_exists = mocker.patch(f"{USER_MANAGER_MODULE_PATH}.user_exists", return_value=False)
    mock_hash_pw = mocker.patch(GENERATE_HASH_PATH, return_value="hashed_password")
    username = "newuser"
    password = "password123"

    # Act
    add_user(username, password)

    # Assert
    mock_user_exists.assert_called_once_with(username)
    mock_hash_pw.assert_called_once_with(password)
    mock_data.add_user.assert_called_once_with(username, "hashed_password")

def test_update_username(mocker):
    """
    Unit test for update_username.
    Verifies it calls the data layer with correct arguments.
    """
    # Arrange
    mock_data = mocker.patch(f"{USER_MANAGER_MODULE_PATH}.data")
    mock_user_exists = mocker.patch(f"{USER_MANAGER_MODULE_PATH}.user_exists", return_value=True)
    old_username = "olduser"
    new_username = "newuser"

    # Act
    update_username(old_username, new_username)

    # Assert
    mock_user_exists.assert_called_once_with(old_username)
    mock_data.update_username.assert_called_once_with(old_username, new_username)

def test_authenticate_user_success(mocker):
    """
    Unit test for authenticate_user with correct credentials.
    """
    # Arrange
    mock_data = mocker.patch(f"{USER_AUTH_MODULE_PATH}.data")
    mock_user = MagicMock()
    mock_user.password_hash = "correct_hash"
    mock_data.get_user_by_username.return_value = mock_user
    mock_check_hash = mocker.patch(CHECK_HASH_PATH, return_value=True)

    # Act
    result = authenticate_user("testuser", "password123")

    # Assert
    mock_data.get_user_by_username.assert_called_once_with("testuser")
    mock_check_hash.assert_called_once_with("correct_hash", "password123")
    assert result is True

def test_authenticate_user_wrong_password(mocker):
    """
    Unit test for authenticate_user with an incorrect password.
    """
    # Arrange
    mock_data = mocker.patch(f"{USER_AUTH_MODULE_PATH}.data")
    mock_user = MagicMock()
    mock_user.password_hash = "correct_hash"
    mock_data.get_user_by_username.return_value = mock_user
    mock_check_hash = mocker.patch(CHECK_HASH_PATH, return_value=False)

    # Act
    result = authenticate_user("testuser", "wrong_password")

    # Assert
    mock_data.get_user_by_username.assert_called_once_with("testuser")
    mock_check_hash.assert_called_once_with("correct_hash", "wrong_password")
    assert result is False

def test_authenticate_user_no_user(mocker):
    """
    Unit test for authenticate_user when the user does not exist.
    """
    # Arrange
    mock_data = mocker.patch(f"{USER_AUTH_MODULE_PATH}.data")
    mock_data.get_user_by_username.return_value = None
    mock_check_hash = mocker.patch(CHECK_HASH_PATH)

    # Act
    result = authenticate_user("nonexistent", "password")

    # Assert
    mock_data.get_user_by_username.assert_called_once_with("nonexistent")
    mock_check_hash.assert_not_called()
    assert result is False

def test_get_selected_stores(mocker):
    """
    Unit test for get_selected_stores.
    Verifies it calls the data layer and returns the result.
    """
    # Arrange
    mock_data = mocker.patch(f"{USER_PREFS_MODULE_PATH}.data")
    mock_stores = [MagicMock(), MagicMock()]
    mock_data.get_user_stores.return_value = mock_stores

    # Act
    result = get_selected_stores("testuser")

    # Assert
    mock_data.get_user_stores.assert_called_once_with("testuser")
    assert result is mock_stores

def test_load_card_list(mocker):
    """
    Unit test for load_card_list.
    Verifies it calls the correct data layer function.
    """
    # Arrange
    mock_data = mocker.patch(f"{USER_CARDS_MODULE_PATH}.data")
    mock_data.get_user_by_username.return_value = True  # Simulate user exists
    mock_cards = [{"card_name": "test card"}]
    mock_data.get_users_cards.return_value = mock_cards

    # Act
    result = load_card_list("testuser")

    # Assert
    mock_data.get_user_by_username.assert_called_once_with("testuser")
    mock_data.get_users_cards.assert_called_once_with("testuser")
    assert result is mock_cards

def test_save_card_list(mocker):
    """
    Unit test for save_card_list.
    Verifies it calls the correct data layer function.
    """
    # Arrange
    mock_data = mocker.patch(f"{USER_CARDS_MODULE_PATH}.data")
    mock_data.get_user_by_username.return_value = True  # Simulate user exists
    card_list = [{"card_name": "test card", "amount": 1}]

    # Act
    save_card_list("testuser", card_list)

    # Assert
    mock_data.get_user_by_username.assert_called_once_with("testuser")
    mock_data.update_user_tracked_cards_list.assert_called_once_with("testuser", card_list)
