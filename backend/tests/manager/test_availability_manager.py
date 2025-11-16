import pytest  # noqa
from unittest.mock import MagicMock, patch
from managers.availability_manager.availability_manager import (
    check_availability,
    get_cached_availability_or_trigger_check,
)


# Mock Card class to simulate the structure of card objects from user_manager
class MockCard:
    def __init__(self, card_name):
        self.card_name = card_name

    def model_dump(self):
        """Simulates Pydantic's model_dump for task queuing."""
        return {"card_name": self.card_name}


@patch(
    "managers.availability_manager.availability_manager."
    "redis_manager.publish_pubsub"
)
def test_check_availability(mock_publish_pubsub):
    """
    Verifies check_availability publishes a command to the scheduler.
    """
    # Arrange
    username = "testuser"
    expected_command = {
        "type": "queue_all_availability_checks",
        "payload": {"username": username},
    }

    # Act
    result = check_availability(username)

    # Assert
    mock_publish_pubsub.assert_called_once_with(
        "scheduler-requests", expected_command
    )
    assert result == {
        "status": "requested",
        "message": "Availability update has been requested.",
    }


@patch(
    "managers.availability_manager.availability_manager.availability_storage"
)
@patch("managers.availability_manager.availability_manager.user_manager")
@patch("managers.availability_manager.availability_manager.database")
def test_get_card_availability_with_cached_data(
    mock_database, mock_user_manager, mock_storage, mocker
):
    """
    Verifies get_cached_availability_or_trigger_check returns cached data
    and does not queue a task.
    """
    # Arrange
    username = "testuser"
    mock_store = MagicMock()
    mock_store.slug = "test-store"
    mock_database.get_user_stores.return_value = [mock_store]
    mock_user_manager.load_card_list.return_value = [MockCard("Test Card")]
    cached_data = [{"price": "1.00"}]
    mock_storage.get_cached_availability_data.return_value = cached_data

    # Act
    cached_results = get_cached_availability_or_trigger_check(username)

    # Assert
    mock_storage.get_cached_availability_data.assert_called_once_with(
        "test-store", "Test Card"
    )
    assert cached_results == {"test-store": {"Test Card": cached_data}}  # noqa


@patch(
    "managers.availability_manager.availability_manager."
    "redis_manager.publish_pubsub"
)
@patch(
    "managers.availability_manager.availability_manager.availability_storage"
)
@patch("managers.availability_manager.availability_manager.user_manager")
@patch("managers.availability_manager.availability_manager.database")
def test_get_card_availability_with_no_cached_data(
    mock_database, mock_user_manager, mock_storage, mock_publish_pubsub, mocker
):
    """
    Verifies get_cached_availability_or_trigger_check queues a fetch task if
    data is not cached.
    """
    # Arrange
    username = "testuser"
    mock_store = MagicMock()
    mock_store.slug = "test-store"
    mock_database.get_user_stores.return_value = [mock_store]
    mock_card = MockCard("Test Card")
    mock_user_manager.load_card_list.return_value = [mock_card]
    mock_storage.get_cached_availability_data.return_value = None
    expected_command = {
        "type": "availability_request",
        "payload": {
            "username": username,
            "store": "test-store",
            "card_data": mock_card.model_dump(),
        },
    }

    # Act
    cached_results = get_cached_availability_or_trigger_check(username)

    # Assert
    mock_storage.get_cached_availability_data.assert_called_once_with(
        "test-store", "Test Card"
    )
    # Verify that a command was published to the scheduler instead of a task
    # being queued directly.
    mock_publish_pubsub.assert_called_once_with(
        "scheduler-requests", expected_command
    )
    assert cached_results == {}


@patch(
    "managers.availability_manager.availability_manager.availability_storage"
)
@patch("managers.availability_manager.availability_manager.user_manager")
@patch("managers.availability_manager.availability_manager.database")
def test_get_card_availability_handles_invalid_store(
    mock_database, mock_user_manager, mock_storage, mocker
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
    get_cached_availability_or_trigger_check(username)

    # Assert
    mock_database.get_user_stores.assert_called_once_with(username)
    mock_user_manager.load_card_list.assert_called_once_with(username)

    # Verify that get_availability_data was only called for the one valid store
    mock_storage.get_cached_availability_data.assert_called_once_with(
        "valid-store",
        "Test Card",
    )
