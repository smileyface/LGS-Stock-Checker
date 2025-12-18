import pytest  # noqa
from unittest.mock import MagicMock, patch
from managers.availability_manager.availability_manager import (
    check_availability,
    get_cached_availability_or_trigger_check,
)
from schema.messaging.messages import AvailabilityRequestCommand


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

    # Act
    result = check_availability(username)

    # Assert
    mock_publish_pubsub.assert_called_once()
    args, _ = mock_publish_pubsub.call_args
    assert isinstance(args[0], AvailabilityRequestCommand)
    assert args[0].channel == "scheduler-requests"
    assert args[0].payload.user.username == username
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
    mock_user_manager.get_user_stores.return_value = [mock_store]
    mock_user_manager.load_card_list.return_value = {"Test Card": {"name": "Test Card"}}
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
    mock_user_manager.get_user_stores.return_value = [mock_store]
    mock_user_manager.load_card_list.return_value = {"Test Card": {"name": "Test Card"}}
    mock_storage.get_cached_availability_data.return_value = None

    # Act
    cached_results = get_cached_availability_or_trigger_check(username)

    # Assert
    mock_storage.get_cached_availability_data.assert_called_once_with(
        "test-store", "Test Card"
    )
    # Verify that a command was published to the scheduler instead of a task
    # being queued directly.
    mock_publish_pubsub.assert_called_once()
    args, _ = mock_publish_pubsub.call_args
    assert isinstance(args[0], AvailabilityRequestCommand)
    assert args[0].channel == "scheduler-requests"
    assert args[0].payload.user.username == username
    assert args[0].payload.store_slug == "test-store"
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

    mock_user_manager.get_user_stores.return_value = [
        mock_store_invalid_slug,
        mock_store_invalid_obj,
        mock_store_valid,
    ]
    mock_user_manager.load_card_list.return_value = {"Test Card": {"name": "Test Card"}}

    # Act
    get_cached_availability_or_trigger_check(username)

    # Assert
    mock_user_manager.get_user_stores.assert_called_once_with(username)
    mock_user_manager.load_card_list.assert_called_once_with(username)

    # Verify that get_availability_data was only called for the one valid store
    mock_storage.get_cached_availability_data.assert_called_once_with(
        "valid-store",
        "Test Card",
    )
