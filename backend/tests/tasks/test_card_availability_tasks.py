import pytest
from unittest.mock import MagicMock, call

from tasks.card_availability_tasks import (
    update_availability_single_card,
    update_all_tracked_cards_availability,
)


@pytest.fixture
def mock_publish_pubsub(mocker):
    """Mocks the redis_manager.publish_worker_result function."""
    return mocker.patch("managers.redis_manager.publish_pubsub")


def test_update_availability_single_card_success(
    mock_store, mock_publish_pubsub, mock_socket_emit_worker
):
    """
    GIVEN a card and store
    WHEN update_availability_single_card is called and finds available items
    THEN it should fetch data, publish the result to Redis,
         and emit socket events.
    """
    # --- Arrange ---
    username = "testuser"
    store_name = "test-store"
    card_name = "Sol Ring"
    card_data = {
        "card_name": card_name,
        "name": card_name,
        "amount": 1,
        "specifications": [],
        "card": {"name": card_name},
        "card_specs": []
    }

    # Mock realistic data matching what CardListingSchema would produce/dump
    available_items = [
        {
            "url": "https://test.com/sol-ring",
            "name": "Sol Ring",
            "set_code": "C21",
            "collector_number": "123",
            "finish": "non-foil",
            "price": 1.99,
            "condition": "NM",
            "quantity": 5
        }
    ]

    mock_store_instance = MagicMock()
    mock_store_instance.fetch_card_availability.return_value = available_items
    mock_store.get_store.return_value = mock_store_instance

    # --- Act ---
    result = update_availability_single_card(username, store_name, card_data)

    # --- Assert ---
    assert result is True
    mock_store.get_store.assert_called_once_with(store_name)
    # The task should unpack card_data to fetch by name and specs
    mock_store_instance.fetch_card_availability.assert_called_once_with(
        card_name, [])

    # Verify result publishing to Redis
    mock_publish_pubsub.assert_called_once()
    published_msg = mock_publish_pubsub.call_args.args[0]

    assert published_msg.name == "availability_result"
    assert published_msg.payload.store.slug == store_name
    assert published_msg.payload.card.card.name == card_name
    assert len(published_msg.payload.items) == 1
    assert published_msg.payload.items[0]["price"] == 1.99

    # Verify socket emission using the worker mock
    expected_calls = [
        call(
            "availability_check_started",
            {"store": store_name, "card": card_name},
            room=username,
        ),
        call(
            "card_availability_data",
            {
                "username": username,
                "store": store_name,
                "card": card_name,
                "items": available_items,
            },
            room=username,
        ),
    ]
    assert mock_socket_emit_worker.call_count == 2
    mock_socket_emit_worker.assert_has_calls(expected_calls, any_order=False)


def test_update_all_tracked_cards_availability(user_factory,
                                               db_session,
                                               mocker):
    """
    GIVEN users exist in the database (via factories)
    WHEN the system-wide task 'update_all_tracked_cards_availability' is called
    THEN it queries the DB and calls the update function for each user.
    """
    # --- Arrange ---
    # Create real users in the test database instead of mocking the DB layer
    user_factory(username="user_alpha")
    user_factory(username="user_beta")

    # Mock the internal function that processes each user
    mock_update_for_user = mocker.patch(
        "tasks.card_availability_tasks.update_availability_for_user"
    )

    # --- Act ---
    update_all_tracked_cards_availability()

    # --- Assert ---
    # Verify that the user-specific update function was called for both users
    expected_calls = [call("user_alpha"), call("user_beta")]

    # Check that calls happened regardless of DB return order
    mock_update_for_user.assert_has_calls(expected_calls, any_order=True)
    assert mock_update_for_user.call_count == 2


def test_update_availability_single_card_no_items_found(
    mock_store, mock_publish_pubsub, mock_socket_emit_worker
):
    """
    GIVEN a card and store
    WHEN update_availability_single_card finds no available items
    THEN it should publish an empty list and emit both start and result events.
    """
    # --- Arrange ---
    username = "testuser"
    store_name = "test-store"
    card_name = "Obscure Card"
    card_data = {
        "card_name": card_name,
        "name": card_name,
        "amount": 1,
        "specifications": [],
        "card": {"name": card_name},
        "card_specs": []
    }

    mock_store_instance = MagicMock()
    mock_store_instance.fetch_card_availability.return_value = []
    mock_store.get_store.return_value = mock_store_instance

    # --- Act ---
    result = update_availability_single_card(username, store_name, card_data)

    # --- Assert ---
    assert result is True

    # Verify publishing was called and check the model
    mock_publish_pubsub.assert_called_once()
    published_msg = mock_publish_pubsub.call_args.args[0]

    assert published_msg.name == "availability_result"
    assert published_msg.payload.store.slug == store_name
    assert published_msg.payload.card.card.name == card_name
    assert len(published_msg.payload.items) == 0

    # Verify socket emission still happens with an empty items list
    expected_calls = [
        call(
            "availability_check_started",
            {"store": store_name, "card": card_name},
            room=username,
        ),
        call(
            "card_availability_data",
            {
                "username": username,
                "store": store_name,
                "card": card_name,
                "items": [],
            },
            room=username,
        ),
    ]
    assert mock_socket_emit_worker.call_count == 2
    mock_socket_emit_worker.assert_has_calls(expected_calls, any_order=False)
