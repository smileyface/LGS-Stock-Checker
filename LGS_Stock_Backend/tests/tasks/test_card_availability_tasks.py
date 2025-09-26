import pytest
from unittest.mock import patch, MagicMock

from tasks.card_availability_tasks import update_availability_single_card


@pytest.fixture
def mock_store_manager():
    """Mocks the store_manager used in the task."""
    with patch("tasks.card_availability_tasks.store_manager") as mock:
        yield mock


@pytest.fixture
def mock_availability_manager():
    """Mocks the availability_manager used in the task."""
    with patch("tasks.card_availability_tasks.availability_manager") as mock:
        yield mock


@pytest.fixture
def mock_socket_emit():
    """Mocks the socket_emit module used in the task."""
    with patch("tasks.card_availability_tasks.socket_emit") as mock:
        yield mock


def test_update_availability_single_card_success(
    mock_store_manager, mock_availability_manager, mock_socket_emit
):
    """
    GIVEN a card and store
    WHEN update_availability_single_card is called and finds available items
    THEN it should fetch data, cache it, and emit a socket event.
    """
    # Arrange
    username = "testuser"
    store_name = "test-store"
    card_data = {"card_name": "Sol Ring", "specifications": []}
    
    mock_store_instance = MagicMock()
    mock_store_instance.fetch_card_availability.return_value = [{"price": 1.99, "condition": "NM"}]
    mock_store_manager.store_list.return_value = mock_store_instance

    # Act
    result = update_availability_single_card(username, store_name, card_data)

    # Assert
    assert result is True
    mock_store_manager.store_list.assert_called_once_with(store_name)
    mock_store_instance.fetch_card_availability.assert_called_once_with("Sol Ring", [])
    
    # Verify caching
    mock_availability_manager.cache_availability_data.assert_called_once_with(
        store_name, "Sol Ring", [{"price": 1.99, "condition": "NM"}]
    )

    # Verify socket emission
    expected_event_data = {
        "username": username,
        "store": store_name,
        "card": "Sol Ring",
        "items": [{"price": 1.99, "condition": "NM"}]
    }
    mock_socket_emit.emit_from_worker.assert_called_once_with(
        "card_availability_data", expected_event_data, room=username
    )


def test_update_availability_single_card_no_items_found(
    mock_store_manager, mock_availability_manager, mock_socket_emit
):
    """
    GIVEN a card and store
    WHEN update_availability_single_card finds no available items
    THEN it should not cache or emit any events.
    """
    # Arrange
    mock_store_instance = MagicMock()
    mock_store_instance.fetch_card_availability.return_value = []
    mock_store_manager.store_list.return_value = mock_store_instance

    # Act
    update_availability_single_card("user", "store", {"card_name": "Card"})

    # Assert
    mock_availability_manager.cache_availability_data.assert_not_called()
    mock_socket_emit.emit_from_worker.assert_not_called()
