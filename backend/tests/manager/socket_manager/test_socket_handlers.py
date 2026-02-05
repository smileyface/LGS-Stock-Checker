import pytest  # noqa

from managers.socket_manager import socket_handlers

from data.database.models.orm_models import (
    User,
    UserTrackedCards,
)


def test_on_add_card_triggers_availability_check(
    db_session,
    user_factory,
    mock_sh_emit,
    mock_sh_trigger_availability_check,
    mock_sh_get_current_user
):
    """
    GIVEN a user exists (via factory)
    WHEN they add a new card via the 'add_card' socket event
    THEN the card is added to the DB, availability check is triggered,
    and the updated list is emitted.
    """
    # Arrange
    # 1. Create a real user.
    # mock_sh_get_current_user is configured to return "testuser" by default
    # in socket_fixtures.py. So we create a user with that name.
    user_factory(username="testuser")

    # 2. Prepare Payload
    card_data_from_client = {
        "name": "add_card",
        "payload": {
            "command": "add",
            "update_data": {
                "card": {"name": "Sol Ring"},
                "amount": 1,
                "card_specs": []
            }
        }
    }

    # Act
    socket_handlers.handle_add_user_tracked_card(card_data_from_client)

    # Assert
    # 1. Verify DB State (Black Box)
    # We check if the card actually ended up in the database.
    tracked_card = db_session.query(UserTrackedCards).join(User).filter(
        User.username == "testuser",
        UserTrackedCards.card_name == "Sol Ring"
    ).first()

    assert tracked_card is not None
    assert tracked_card.amount == 1

    # 2. Verify Availability Check Triggered
    # We still mock this because we don't want to spin up Redis/Workers here
    mock_sh_trigger_availability_check.assert_called_once()

    call_args = mock_sh_trigger_availability_check.call_args
    assert call_args.args[0] == "testuser"
    assert call_args.args[1]["card"]["name"] == "Sol Ring"

    # 3. Verify Emission via Callback
    # Execute the callback passed to the trigger function
    callback = call_args.kwargs.get("on_complete_callback")
    assert callback is not None

    callback()  # This triggers user_manager.send_user_cards("testuser")

    # Verify the emit happened with the correct data structure
    mock_sh_emit.assert_called()

    # Find the 'cards_data' emission
    emit_calls = [
        c for c in mock_sh_emit.call_args_list 
        if c.args[0] == "cards_data"
    ]
    assert len(emit_calls) > 0

    last_call = emit_calls[-1]
    event_name = last_call.args[0]
    # Check payload which might be arg 1 or 2 depending on how emit is called
    payload = last_call.args[1]
    kwargs = last_call.kwargs

    assert "payload" in payload
    payload = payload["payload"]

    assert event_name == "cards_data"
    assert kwargs.get("to") == "testuser"

    # Verify the payload contains our new card
    # Payload structure: {"username": str, "cards": list}
    assert "cards" in payload
    cards_list = payload["cards"]
    assert any(c["card"]["name"] == "Sol Ring" for c in cards_list)


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
def test_on_add_card_with_invalid_data(mock_sh_get_current_user,
                                       mock_sh_emit,
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
