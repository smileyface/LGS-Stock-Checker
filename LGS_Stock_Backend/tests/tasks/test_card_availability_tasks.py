import pytest
from unittest.mock import MagicMock, call

from tasks.card_availability_tasks import (
    update_availability_single_card,
    update_all_tracked_cards_availability,
)


@pytest.fixture
def mock_publish_worker_result(mocker):
    """Mocks the redis_manager.publish_worker_result function."""
    return mocker.patch("managers.redis_manager.publish_worker_result")


def test_update_availability_single_card_success(mock_store, mock_publish_worker_result, mock_socket_emit):
    """
    GIVEN a card and store
    WHEN update_availability_single_card is called and finds available items
    THEN it should fetch data, publish the result to Redis, and emit socket events.
    """
    # Arrange
    username = "testuser"
    store_name = "test-store"
    card_data = {"card_name": "Sol Ring", "specifications": []}
    available_items = [{"price": 1.99, "condition": "NM"}]

    mock_store_instance = MagicMock()
    mock_store_instance.fetch_card_availability.return_value = available_items
    mock_store.get_store.return_value = mock_store_instance

    # Act
    result = update_availability_single_card(username, store_name, card_data)

    # Assert
    assert result is True
    mock_store.get_store.assert_called_once_with(store_name)
    mock_store_instance.fetch_card_availability.assert_called_once_with("Sol Ring", [])

    # Verify result publishing
    mock_publish_worker_result.assert_called_once_with(
        "worker-results",
        {"type": "availability_result", "payload": {"store": store_name, "card": "Sol Ring", "items": available_items}},
    )

    # Verify socket emission
    # The task should emit two events: one when it starts, one when it finishes.
    expected_calls = [
        call("availability_check_started", {"store": store_name, "card": "Sol Ring"}, room=username),
        call(
            "card_availability_data",
            {
                "username": username,
                "store": store_name,
                "card": "Sol Ring",
                "items": available_items,
            },
            room=username,
        ),
    ]
    assert mock_socket_emit.call_count == 2
    mock_socket_emit.assert_has_calls(expected_calls, any_order=False)


def test_update_all_tracked_cards_availability(mocker):
    """
    GIVEN a list of users exists in the database
    WHEN the system-wide task 'update_all_tracked_cards_availability' is called
    THEN it should call the user-specific update function for each user.
    This test covers requirement [5.1.7].
    """
    # Arrange
    # 1. Mock the database call to return a list of users
    mock_db = mocker.patch("tasks.card_availability_tasks.database")
    mock_user1 = MagicMock()
    mock_user1.username = "user1"
    mock_user2 = MagicMock()
    mock_user2.username = "user2"
    mock_db.get_all_users.return_value = [mock_user1, mock_user2]

    # 2. Mock the user-specific task function that gets called
    mock_update_for_user = mocker.patch(
        "tasks.card_availability_tasks.update_availability_for_user"
    )

    # Act
    update_all_tracked_cards_availability()

    # Assert
    # Verify that the database was queried for all users
    mock_db.get_all_users.assert_called_once()

    # Verify that the user-specific update function was called for each user
    expected_calls = [call("user1"), call("user2")]
    mock_update_for_user.assert_has_calls(expected_calls, any_order=True)
    assert mock_update_for_user.call_count == 2


def test_update_availability_single_card_no_items_found(mock_store, mock_publish_worker_result, mock_socket_emit): # noqa
    """
    GIVEN a card and store
    WHEN update_availability_single_card finds no available items
    THEN it should publish an empty list and emit both start and result events.
    """
    # Arrange
    username = "testuser"
    store_name = "test-store"
    card_data = {"card_name": "Obscure Card", "specifications": []}

    mock_store_instance = MagicMock()
    mock_store_instance.fetch_card_availability.return_value = []
    mock_store.get_store.return_value = mock_store_instance

    # Act
    result = update_availability_single_card(username, store_name, card_data)

    # Assert
    assert result is True
    mock_publish_worker_result.assert_called_once_with(
        "worker-results",
        {"type": "availability_result", "payload": {"store": store_name, "card": "Obscure Card", "items": []}}
    )

    # Verify socket emission still happens, but with an empty items list
    expected_calls = [
        call("availability_check_started", {"store": store_name, "card": "Obscure Card"}, room=username),
        call(
            "card_availability_data",
            {"username": username, "store": store_name, "card": "Obscure Card", "items": []},
            room=username,
        ),
    ]
    assert mock_socket_emit.call_count == 2
    mock_socket_emit.assert_has_calls(expected_calls, any_order=False)
