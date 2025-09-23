import pytest
from unittest.mock import patch
from tasks.card_availability_tasks import update_availability_single_card
import data
import managers


@pytest.fixture
def mock_store():
    """Mocks the store_manager.store_list function."""
    with patch("LGS_Stock_Backend.tasks.card_availability_tasks.store_manager.store_list") as mock:
        yield mock


@pytest.fixture
def mock_cache_availability():
    """Mocks the availability_manager.cache_availability_data function."""
    with patch("LGS_Stock_Backend.tasks.card_availability_tasks.availability_manager.cache_availability_data") as mock:
        yield mock


@pytest.fixture
def mock_socket_emit():
    """Mocks the socket_emit.emit_from_worker function."""
    with patch("LGS_Stock_Backend.tasks.card_availability_tasks.socket_emit.emit_from_worker") as mock:
        yield mock


def test_update_availability_single_card_success(mock_store, mock_cache_availability, mock_socket_emit):
    """
    GIVEN a valid username, store_name, and card
    WHEN update_availability_single_card is called
    THEN it should successfully fetch availability, cache it, and emit a socket event.
    """
    # Arrange
    username = "testuser"
    store_name = "test_store"
    card = {"card_name": "Test Card", "specifications": {}}
    available_items = [{"name": "Item 1", "price": 10.0}]

    # Configure the mock store instance and its method's return value
    mock_store_instance = mock_store.return_value
    mock_store_instance.fetch_card_availability.return_value = available_items

    # Act
    result = update_availability_single_card(username, store_name, card)

    # Assert
    assert result is True
    mock_store.assert_called_once_with(store_name)
    mock_store_instance.fetch_card_availability.assert_called_once_with("Test Card", {})
    mock_cache_availability.assert_called_once_with(store_name, "Test Card", available_items)
    mock_socket_emit.assert_called_once_with("card_availability_data",
                                             {"username": username, "store": store_name, "card": "Test Card",
                                              "items": available_items}, room=username)


def test_update_availability_single_card_invalid_store(mock_store):
    """
    GIVEN an invalid store_name
    WHEN update_availability_single_card is called
    THEN it should log a warning and return False.
    """
    # Arrange
    username = "testuser"
    store_name = "invalid_store"
    card = {"card_name": "Test Card", "specifications": {}}
    mock_store.return_value = None

    # Act
    result = update_availability_single_card(username, store_name, card)

    # Assert
    assert result is False
    mock_store.assert_called_once_with(store_name)


def test_update_availability_single_card_missing_card_name(mock_store):
    """
    GIVEN a card dictionary without a card_name
    WHEN update_availability_single_card is called
    THEN it should log an error and return False.
    """
    # Arrange
    username = "testuser"
    store_name = "test_store"
    card = {"specifications": {}}  # Missing card_name

    # Act
    result = update_availability_single_card(username, store_name, card)

    # Assert
    assert result is False
    # Ensure that `store_manager.store_list` is not called,
    # as the function should exit before that point
    mock_store.assert_not_called()
