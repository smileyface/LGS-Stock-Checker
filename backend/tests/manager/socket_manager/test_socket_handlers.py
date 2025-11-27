import pytest  # noqa

from managers.socket_manager import socket_handlers
from schema.messaging import CardSpecsSchema


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
    # 1. Verify the card was added to the user's list with the
    # correct arguments
    mock_sh_user_manager.add_user_card.assert_called_once_with(
        username,
        "Sol Ring",
        1,
        CardSpecsSchema(set_code=None, collector_number=None, finish=None),
    )

    # 2. Verify availability check was triggered for the new card ([5.1.6])
    # The availability check uses a dictionary representation
    card_data_for_task = {
        "card_name": "Sol Ring",
        "specifications": CardSpecsSchema(
            set_code=None, collector_number=None, finish=None
        ),
    }
    mock_sh_trigger_availability_check.assert_called_once()
    # Check the positional arguments passed to the trigger function
    assert mock_sh_trigger_availability_check.call_args.args[0] == username
    assert mock_sh_trigger_availability_check.call_args.args[1] == card_data_for_task
    # Check that a callback was passed
    assert "on_complete_callback" in mock_sh_trigger_availability_check.call_args.kwargs

    # 3. Verify the client was notified with the updated card list via
    # the callback
    # To test this properly, we execute the callback that was passed to
    # the mock
    callback = mock_sh_trigger_availability_check.call_args.kwargs[
        "on_complete_callback"
    ]
    callback()
    mock_sh_emit.assert_called_with(
        "cards_data",
        {"username": "testuser", "tracked_cards": []},
        room="testuser",
    )


@pytest.mark.parametrize(
    "invalid_data, expected_error_part",
    [
        # Missing all fields
        ({}, "Field required"),
        # Missing amount
        ({"card": "Sol Ring"}, "Field required"),
        # Missing card name
        ({"amount": 1}, "Field required"),
        # Empty card name
        ({"card": "", "amount": 1}, "at least 1 character"),
        # Invalid amount
        ({"card": "Sol Ring", "amount": 0}, "greater than 0"),
        # Invalid finish
        (
            {"card": "Sol Ring", "amount": 1, "card_specs": {
                "finish": "invalid"}},
            "Input should be",
        ),
    ],
)
def test_on_add_card_with_invalid_data(mock_sh_emit,
                                       invalid_data,
                                       expected_error_part):
    """
    GIVEN invalid data for the 'add_card' event
    WHEN the handler is called
    THEN it should emit a validation error and not proceed.
    """
    socket_handlers.handle_add_user_tracked_card(invalid_data)
    mock_sh_emit.assert_called_once()
    assert mock_sh_emit.call_args.args[0] == "error"
    assert expected_error_part in str(mock_sh_emit.call_args.args[1])


@pytest.mark.parametrize(
    "invalid_data, expected_error_part",
    [
        ({}, "Field required"),  # Missing all fields
        ({"card": "Sol Ring"}, "Field required"),  # Missing update_data
        ({"update_data": {}}, "Field required"),  # Missing card name
        (
            {
                "card": "Sol Ring",
                "update_data":
                {
                    "specifications":
                        {"finish": "invalid"}
                },
            },
            "Invalid data for update_card: 1 validation error",
        ),  # Invalid finish
    ],
)
def test_on_update_card_with_invalid_data(
    seeded_user_with_cards,
    mock_sh_emit,
    mock_sh_get_current_user,
    invalid_data,
    expected_error_part,
):
    """
    GIVEN invalid data for the 'update_card' event
    WHEN the handler is called
    THEN it should emit a validation error and not proceed.
    """

    socket_handlers.handle_update_user_tracked_cards(invalid_data)
    mock_sh_emit.assert_called_once()
    assert mock_sh_emit.call_args.args[0] == "error"
    assert expected_error_part in str(mock_sh_emit.call_args.args[1])


@pytest.mark.parametrize(
    "invalid_data, expected_log_part",
    [
        (
            {"card": "Sol Ring", "update_data": {"amount": 0}},
            "Input should be greater than or equal to 1 ["
            "type=greater_than_equal, input_value=0, input_type=int]",
        ),  # Invalid amount
    ]
)
def test_on_update_card_with_non_critical_invalid_data(
    seeded_user_with_cards,
    mock_sh_get_current_user,
    caplog,
    invalid_data,
    expected_log_part,
):
    """
    GIVEN non-critical invalid data for the 'update_card' event
    WHEN the event handler is called
    THEN it should log a warning, not update the field, but update
         other fields.
    """
    socket_handlers.handle_update_user_tracked_cards(invalid_data)
    assert expected_log_part in caplog.text


@pytest.mark.parametrize(
    "invalid_data, expected_error_part",
    [
        ({}, "Field required"),  # Missing card field
        # Empty card name
        ({"card": ""}, "String should have at least 1 character"),
    ],
)
def test_on_delete_card_with_invalid_data(
    mock_sh_emit, invalid_data, expected_error_part
):
    """
    GIVEN invalid data for the 'delete_card' event
    WHEN the handler is called
    THEN it should emit a validation error and not proceed.
    """
    socket_handlers.handle_delete_user_tracked_card(invalid_data)
    mock_sh_emit.assert_called_once()
    assert mock_sh_emit.call_args.args[0] == "error"
    assert expected_error_part in str(mock_sh_emit.call_args.args[1])


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
            "finishes": ["foil", "non-foil"],
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
    mock_sh_emit.assert_called_once_with("card_printings_data",
                                         expected_payload)


@pytest.mark.parametrize(
    "invalid_data",
    [
        {},
        {"card_name": ""},
    ],
)
def test_handle_get_card_printings_invalid_data(mock_sh_emit, invalid_data):
    """
    GIVEN invalid data for the 'get_card_printings' event
    WHEN the handler is called
    THEN it should raise a validation error and not emit anything.
    """
    with pytest.raises(Exception):  # Pydantic raises ValidationError
        socket_handlers.handle_get_card_printings(data=invalid_data)
    mock_sh_emit.assert_not_called()
