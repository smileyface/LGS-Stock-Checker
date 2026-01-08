import pytest  # noqa

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
    card_data_from_client = {
        "name": "add_card",
        "payload": {
            "command": "add",
            "update_data": {
                "card": {
                    "name": "Sol Ring"
                },
                "amount": 1,
                "card_specs": [{}]
            }
        }
    }

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
        {"set_code": None, "collector_number": None, "finish": None}
    )

    # 2. Verify availability check was triggered for the new card ([5.1.6])
    # The availability check uses a dictionary representation
    card_data_for_task = {
        "card": {
            "name": "Sol Ring"},
        "specifications": {
            "set_code": None,
            "collector_number": None,
            "finish": None},
    }
    mock_sh_trigger_availability_check.assert_called_once()
    # Check the positional arguments passed to the trigger function
    assert mock_sh_trigger_availability_check.call_args.args[0] == username
    assert (mock_sh_trigger_availability_check.call_args.args[1] ==
            card_data_for_task)
    # Check that a callback was passed
    assert ("on_complete_callback" in
            mock_sh_trigger_availability_check.call_args.kwargs)

    # 3. Verify the client was notified with the updated card list via
    # the callback
    # To test this properly, we execute the callback that was passed to
    # the mock
    callback = mock_sh_trigger_availability_check.call_args.kwargs[
        "on_complete_callback"
    ]
    callback()
    expected_message = {
        "name": "cards_data",
        "payload": {"cards": []}
    }
    mock_sh_emit.assert_called_with(
        "cards_data",
        expected_message,
        to="testuser",
    )


@pytest.mark.parametrize(
    "invalid_data, expected_error_part",
    [
        # Missing all fields
        ({}, "Field required"),
        # Missing amount
        ({
            "payload": {
                "command": "add",
                "update_data": {"card": {"name": "Sol Ring"}}
            }
        }, "Field required"),
        # Missing card name
        ({
            "payload": {
                "command": "add",
                "update_data": {"amount": 1}
            }
        }, "Field required"),
        # Empty card name
        ({
            "payload": {
                "command": "add",
                "update_data": {"card": {"name": ""}, "amount": 1}
            }
        }, "at least 1 character"),
        # Invalid amount
        ({
            "payload": {
                "command": "add",
                "update_data": {"card": {"name": "Sol Ring"}, "amount": 0}
            }
        }, "greater than 0"),
        # Negative amount
        ({
            "payload": {
                "command": "add",
                "update_data": {"card": {"name": "Sol Ring"}, "amount": -3}
            }
        }, "greater than 0"),
        # Invalid finish
        ({
            "payload": {
                "command": "add",
                "update_data": {
                    "card": {"name": "Sol Ring"},
                    "amount": 1,
                    "card_specs": {"finish": "invalid"},
                }
            }
        }, "Input should be"),
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
        ({}, "Field required"),
        # Missing update_data
        ({
            "payload": {
                "command": "update"
            }
        }, "Field required"),
        # Missing card name
        ({
            "payload": {
                "command": "update",
                "update_data": {}
            }
        }, "Field required"),
        # Invalid Finish
        ({
            "payload": {
                "command": "update",
                "update_data": {
                    "card": {"name": "Sol Ring"},
                    "amount": 1,
                    "card_specs": {"finish": "invalid"}
                }
            }
        }, "Input should be"),
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
    # Check that at least one error message contains the expected part
    assert mock_sh_emit.call_args.args[0] == "server_log"
    assert expected_error_part in str(mock_sh_emit.call_args.args[1])


@pytest.mark.parametrize(
    "invalid_data, expected_error_part",
    [
        ({}, "Field required"),  # Missing card field
        # Empty card name
        ({
            "payload": {
                "command": "delete",
                "update_data": {
                    "card": {"name": ""}
                }
            }
        }, "at least 1 character"),
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
    client_data = {
        "name": "get_card_printings",
        "payload": {"card": {"name": card_name}}
    }
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
    expected_message = {
        "name": "card_printings_data",
        "payload": {"card_name": card_name, "printings": mock_printings}
    }
    mock_sh_emit.assert_called_once_with("card_printings_data",
                                         expected_message,
                                         to="")


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


@pytest.mark.parametrize(
    "fixture_name, username, expect_emit",
    [
        ("seeded_user_with_cards", "testuser", True),
        ("seeded_user", "testuser", True),
        ("seeded_user", "", False),
    ],
    ids=["success", "empty_list", "missing_username"]
)
def test_send_user_cards(request, mock_sh_emit, fixture_name,
                         username, expect_emit):
    """
    GIVEN a username and a database state (seeded with cards or empty)
    WHEN _send_user_cards is called
    THEN it should fetch from the DB and emit the correct 'cards_data' event.
    """
    # Arrange
    # Initialize the database state using the fixture
    request.getfixturevalue(fixture_name)

    # Act
    socket_handlers.send_user_cards(username)

    # Assert
    if expect_emit:
        mock_sh_emit.assert_called_once()
        args, kwargs = mock_sh_emit.call_args
        assert args[0] == "cards_data"
        assert kwargs["to"] == username

        actual_payload = args[1]["payload"]
        actual_cards = actual_payload["cards"]

        if fixture_name == "seeded_user_with_cards":
            # Verify the presence of seeded cards
            # We check for specific cards known to be in the fixture
            card_names = [c["card"]["name"] for c in actual_cards]
            assert "Lightning Bolt" in card_names
            assert "Counterspell" in card_names
            assert "Sol Ring" in card_names

            # Spot check one card's details
            bolt = next(c for c in actual_cards
                        if c["card"]["name"] == "Lightning Bolt")
            assert bolt["amount"] == 4
            assert len(bolt["card_specs"]) == 2
        else:
            # For seeded_user (empty list)
            assert actual_cards == []
    else:
        mock_sh_emit.assert_not_called()
