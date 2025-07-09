import pytest
from unittest.mock import MagicMock, patch

from managers.user_manager import (
    get_user,
    add_user,
    update_username,
    authenticate_user,
    get_selected_stores,
    load_card_list,
    save_card_list,
)

# The path to the modules/functions as they are *seen* by the user_manager module.
DATA_LAYER_PATH = "managers.user_manager.data"
GENERATE_HASH_PATH = "managers.user_manager.generate_password_hash"
CHECK_HASH_PATH = "managers.user_manager.check_password_hash"


@pytest.fixture
def mock_data_layer(mocker):
    """Mocks the entire 'data' module used by the user_manager."""
    return mocker.patch(DATA_LAYER_PATH)


def test_get_user(mock_data_layer):
    """
    Unit test for get_user.
    Verifies it calls the data layer and returns the result.
    """
    # Arrange
    mock_user = MagicMock()
    mock_data_layer.get_user_by_username.return_value = mock_user
    username = "testuser"

    # Act
    result = get_user(username)

    # Assert
    mock_data_layer.get_user_by_username.assert_called_once_with(username)
    assert result is mock_user


def test_add_user(mocker, mock_data_layer):
    """
    Unit test for add_user.
    Verifies it hashes the password and calls the data layer.
    """
    # Arrange
    mock_hash_pw = mocker.patch(GENERATE_HASH_PATH, return_value="hashed_password")
    username = "newuser"
    password = "password123"

    # Act
    add_user(username, password)

    # Assert
    mock_hash_pw.assert_called_once_with(password)
    mock_data_layer.add_user.assert_called_once_with(username, "hashed_password")


def test_update_username(mock_data_layer):
    """
    Unit test for update_username.
    Verifies it calls the data layer with correct arguments.
    """
    # Arrange
    old_username = "olduser"
    new_username = "newuser"

    # Act
    update_username(old_username, new_username)

    # Assert
    mock_data_layer.update_username.assert_called_once_with(old_username, new_username)


def test_authenticate_user_success(mocker, mock_data_layer):
    """
    Unit test for authenticate_user with correct credentials.
    """
    # Arrange
    mock_user = MagicMock()
    mock_user.password_hash = "correct_hash"
    mock_data_layer.get_user_by_username.return_value = mock_user
    mock_check_hash = mocker.patch(CHECK_HASH_PATH, return_value=True)

    # Act
    result = authenticate_user("testuser", "password123")

    # Assert
    mock_data_layer.get_user_by_username.assert_called_once_with("testuser")
    mock_check_hash.assert_called_once_with("correct_hash", "password123")
    assert result is True


def test_authenticate_user_wrong_password(mocker, mock_data_layer):
    """
    Unit test for authenticate_user with an incorrect password.
    """
    # Arrange
    mock_user = MagicMock()
    mock_user.password_hash = "correct_hash"
    mock_data_layer.get_user_by_username.return_value = mock_user
    mock_check_hash = mocker.patch(CHECK_HASH_PATH, return_value=False)

    # Act
    result = authenticate_user("testuser", "wrong_password")

    # Assert
    mock_data_layer.get_user_by_username.assert_called_once_with("testuser")
    mock_check_hash.assert_called_once_with("correct_hash", "wrong_password")
    assert result is False


def test_authenticate_user_no_user(mocker, mock_data_layer):
    """
    Unit test for authenticate_user when the user does not exist.
    """
    # Arrange
    mock_data_layer.get_user_by_username.return_value = None
    mock_check_hash = mocker.patch(CHECK_HASH_PATH)

    # Act
    result = authenticate_user("nonexistent", "password")

    # Assert
    mock_data_layer.get_user_by_username.assert_called_once_with("nonexistent")
    mock_check_hash.assert_not_called()
    assert result is False


def test_get_selected_stores(mock_data_layer):
    """
    Unit test for get_selected_stores.
    Verifies it calls the data layer and returns the result.
    """
    # Arrange
    mock_stores = [MagicMock(), MagicMock()]
    mock_data_layer.get_user_stores.return_value = mock_stores

    # Act
    result = get_selected_stores("testuser")

    # Assert
    mock_data_layer.get_user_stores.assert_called_once_with("testuser")
    assert result is mock_stores


def test_load_card_list(mock_data_layer):
    """
    Unit test for load_card_list.
    Verifies it calls the correct data layer function.
    """
    # Arrange
    mock_cards = [{"card_name": "test card"}]
    mock_data_layer.get_users_cards_with_specifications.return_value = mock_cards

    # Act
    result = load_card_list("testuser")

    # Assert
    mock_data_layer.get_users_cards_with_specifications.assert_called_once_with("testuser")
    assert result is mock_cards


def test_save_card_list(mock_data_layer):
    """
    Unit test for save_card_list.
    Verifies it calls the correct data layer function.
    """
    # Arrange
    card_list = [{"card_name": "test card", "amount": 1}]

    # Act
    save_card_list("testuser", card_list)

    # Assert
    mock_data_layer.update_user_tracked_cards_list.assert_called_once_with("testuser", card_list)
