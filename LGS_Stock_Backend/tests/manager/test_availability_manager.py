import pytest
from unittest.mock import MagicMock, patch

from managers.availability_manager.availability_manager import (
    check_availability,
    get_card_availability,
)

# Base path for patching dependencies as they are seen by the availability_manager module.
AVAILABILITY_MANAGER_MODULE_PATH = "managers.availability_manager.availability_manager"


# Mock Card class to simulate the structure of card objects from user_manager
class MockCard:
    def __init__(self, card_name):
        self.card_name = card_name

    def model_dump(self):
        """Simulates Pydantic's model_dump for task queuing."""
        return {"card_name": self.card_name}


@patch(f"{AVAILABILITY_MANAGER_MODULE_PATH}.redis_manager")
def test_check_availability(mock_redis_manager):
    """
    Verifies check_availability queues an update task for the specified user.
    """
    # Arrange
    username = "testuser"

    # Act
    result = check_availability(username)

    # Assert
    mock_redis_manager.queue_task.assert_called_once_with(
        "update_wanted_cards_availability", username
    )
    assert result == {
        "status": "queued",
        "message": "Availability update has been triggered.",
    }


@patch(f"{AVAILABILITY_MANAGER_MODULE_PATH}.socket_manager")
@patch(f"{AVAILABILITY_MANAGER_MODULE_PATH}.redis_manager")
@patch(f"{AVAILABILITY_MANAGER_MODULE_PATH}.availability_storage")
@patch(f"{AVAILABILITY_MANAGER_MODULE_PATH}.user_manager")
@patch(f"{AVAILABILITY_MANAGER_MODULE_PATH}.database")
def test_get_card_availability_with_cached_data(
    mock_database, mock_user_manager, mock_storage, mock_redis, mock_socket
):
    """
    Verifies get_card_availability uses and emits cached data if available.
    """
    # Arrange
    username = "testuser"
    mock_store = MagicMock()
    mock_store.slug = "test-store"
    mock_store.name = "Test Store"
    mock_database.get_user_stores.return_value = [mock_store]
    mock_user_manager.load_card_list.return_value = [MockCard("Test Card")]
    cached_data = [{"price": "1.00"}]
    mock_storage.get_availability_data.return_value = cached_data

    # Act
    result = get_card_availability(username)

    # Assert
    mock_storage.get_availability_data.assert_called_once_with("test-store", "Test Card")
    mock_socket.socket_emit.emit_card_availability_data.assert_called_once_with(
        username, "Test Store", "Test Card", cached_data
    )
    mock_redis.queue_task.assert_not_called()
    assert result["status"] == "processing"


@patch(f"{AVAILABILITY_MANAGER_MODULE_PATH}.socket_manager")
@patch(f"{AVAILABILITY_MANAGER_MODULE_PATH}.redis_manager")
@patch(f"{AVAILABILITY_MANAGER_MODULE_PATH}.availability_storage")
@patch(f"{AVAILABILITY_MANAGER_MODULE_PATH}.user_manager")
@patch(f"{AVAILABILITY_MANAGER_MODULE_PATH}.database")
def test_get_card_availability_with_no_cached_data(
    mock_database, mock_user_manager, mock_storage, mock_redis, mock_socket
):
    """
    Verifies get_card_availability queues a fetch task if data is not cached.
    """
    # Arrange
    username = "testuser"
    mock_store = MagicMock()
    mock_store.slug = "test-store"
    mock_store.name = "Test Store"
    mock_database.get_user_stores.return_value = [mock_store]
    mock_card = MockCard("Test Card")
    mock_user_manager.load_card_list.return_value = [mock_card]
    mock_storage.get_availability_data.return_value = None

    # Act
    result = get_card_availability(username)

    # Assert
    mock_storage.get_availability_data.assert_called_once_with("test-store", "Test Card")
    mock_socket.socket_emit.emit_card_availability_data.assert_not_called()
    mock_redis.queue_task.assert_called_once_with(
        "managers.tasks_manager.availability_tasks.update_availability_single_card",
        username,
        "test-store",
        mock_card.model_dump(),
    )
    assert result["status"] == "processing"


@patch(f"{AVAILABILITY_MANAGER_MODULE_PATH}.availability_storage")
@patch(f"{AVAILABILITY_MANAGER_MODULE_PATH}.user_manager")
@patch(f"{AVAILABILITY_MANAGER_MODULE_PATH}.database")
def test_get_card_availability_handles_invalid_store(
    mock_database, mock_user_manager, mock_storage
):
    """
    Verifies that stores with no slug are skipped gracefully.
    """
    # Arrange
    username = "testuser"
    mock_store_valid = MagicMock()
    mock_store_valid.slug = "valid-store"
    mock_store_valid.name = "Valid Store"
    mock_store_invalid_slug = MagicMock()
    mock_store_invalid_slug.slug = None
    mock_store_invalid_slug.name = "Invalid Store"
    mock_store_invalid_obj = None

    mock_database.get_user_stores.return_value = [
        mock_store_invalid_slug,
        mock_store_invalid_obj,
        mock_store_valid,
    ]
    mock_user_manager.load_card_list.return_value = [MockCard("Test Card")]

    # Act
    get_card_availability(username)

    # Assert
    mock_database.get_user_stores.assert_called_once_with(username)
    mock_user_manager.load_card_list.assert_called_once_with(username)

    # Verify that get_availability_data was only called for the one valid store
    mock_storage.get_availability_data.assert_called_once_with(
        "valid-store", "Test Card"
    )