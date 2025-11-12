import pytest
from unittest.mock import MagicMock, call

from managers.socket_manager import socket_handlers


def test_on_add_card_triggers_availability_check(
    mock_sh_user_manager,
    mock_sh_get_current_user,
    mock_sh_emit,
    mock_sh_trigger_availability_check,
):
    """
    GIVEN a user with preferred stores
    WHEN they add a new card via the 'add_card' socket event
    THEN the card is added, an availability check is queued for each store,
    and the updated card list is emitted back to the user.
    """
    # Arrange
    username = "testuser"
    # This data must match the AddCardSchema
    card_data_from_client = {"card": "Sol Ring", "amount": 1, "card_specs": {}}

    # Mock the return value for the full card list after adding
    mock_sh_user_manager.load_card_list.return_value = []

    # Act
    socket_handlers.handle_add_user_tracked_card(card_data_from_client)

    # Assert
    # 1. Verify the card was added to the user's list with the correct arguments
    mock_sh_user_manager.add_user_card.assert_called_once_with(
        username, "Sol Ring", 1, {}
    )

    # 2. Verify availability check was triggered for the new card ([5.1.6])
    card_data_for_task = {"card_name": "Sol Ring", "specifications": {}}
    mock_sh_trigger_availability_check.assert_called_once()
    # Check the positional arguments passed to the trigger function
    assert mock_sh_trigger_availability_check.call_args.args[0] == username
    assert (
        mock_sh_trigger_availability_check.call_args.args[1]
        == card_data_for_task
    )
    # Check that a callback was passed
    assert (
        "on_complete_callback"
        in mock_sh_trigger_availability_check.call_args.kwargs
    )

    # 3. Verify the client was notified with the updated card list via the callback
    # To test this properly, we execute the callback that was passed to the mock
    callback = mock_sh_trigger_availability_check.call_args.kwargs[
        "on_complete_callback"
    ]
    callback()
    mock_sh_emit.assert_called_with(
        "cards_data",
        {"username": "testuser", "tracked_cards": []},
        room="testuser",
    )


def test_handle_get_card_printings(mock_sh_emit, mock_sh_database):
    """
    GIVEN a card name
    WHEN a client emits 'get_card_printings'
    THEN the handler should fetch the printing data and emit it back.
    """
    # Arrange
    card_name = "Sol Ring"
    client_data = {"card_name": card_name}
    mock_printings = [
        {
            "set_code": "C21",
            "collector_number": "125",
            "finishes": ["foil", "nonfoil"],
        }
    ]
    # Configure the mock provided by the fixture
    mock_sh_database.is_card_in_catalog.return_value = True
    mock_sh_database.get_printings_for_card.return_value = mock_printings

    # Act
    socket_handlers.handle_get_card_printings(data=client_data)

    # Assert
    mock_sh_database.is_card_in_catalog.assert_called_once_with(card_name)
    mock_sh_database.get_printings_for_card.assert_called_once_with(card_name)
    expected_payload = {"card_name": card_name, "printings": mock_printings}
    mock_sh_emit.assert_called_once_with(
        "card_printings_data", expected_payload
    )
