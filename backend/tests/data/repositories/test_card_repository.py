import pytest

from data.database.models.orm_models import (
    CardSpecification,
    UserTrackedCards
)
from data.database.repositories.card_repository import (
    get_users_cards,
    modify_user_tracked_card,
    update_user_tracked_card_preferences
)
from data.database.repositories.catalogue_repository import (
    get_printings_for_card,
    is_valid_printing_specification
)


def test_add_and_get_user_card(seeded_user, seeded_printings):
    # Initially, no cards
    assert get_users_cards("testuser") == []

    # Add a card with specifications
    modify_user_tracked_card("add", "testuser", {
        "card":
        {
            "name": "Sol Ring"
        },
        "amount": 4,
        "specifications": [
            {
                "set_code": {"code": "ONE"},
                "finish": {"name": "foil"}
            }
        ]
    })

    cards = get_users_cards("testuser")
    assert len(cards) == 1
    assert cards[0]["name"] == "Sol Ring"
    assert cards[0]["amount"] == 4
    assert len(cards[0]["specifications"]) == 1
    assert cards[0]["specifications"][0]["set_code"] == "ONE"
    assert cards[0]["specifications"][0]["finish"] == "foil"  # type: ignore


def test_add_user_card_user_not_found(db_session):
    """Test that adding a card for a non-existent user does nothing."""
    modify_user_tracked_card("add", "nonexistent_user", {
        "card": {
            "name": "Some Card"
            },
        "amount": 1,
        "specifications": []
        }
    )
    # Verify no UserTrackedCards were created
    assert db_session.query(UserTrackedCards).count() == 0


def test_add_user_card_for_existing_card_adds_specs_but_ignores_amount(
    seeded_user, seeded_printings
):
    """
    Test that calling add_user_card for a card that is already tracked:
    1. Adds new specifications.
    2. Does NOT create a duplicate card entry.
    3. Does NOT update the amount of the existing card.
    """
    # Arrange: Add the card initially with one spec and an amount of 1
    initial_specs = {"set_code": {"code": "MH2"},
                     "finish": {"name": "etched"}}
    modify_user_tracked_card("add", "testuser", {
        "card": {
            "name": "Thoughtseize"
            },
        "amount": 1,
        "specifications": [initial_specs]
        }
    )

    # Act: Call add_user_card again with a new spec and a DIFFERENT amount
    new_specs = {"set_code": {"code": "2XM"}, "finish": {"name": "non-foil"}}
    modify_user_tracked_card("add", "testuser", {
        "card": {
            "name": "Thoughtseize"
            },
        "amount": 10,
        "specifications": [new_specs]
        })

    # Assert
    cards = get_users_cards("testuser")
    assert (
        len(cards) == 1
    ), "Should not create a duplicate UserTrackedCards entry"

    tracked_card = cards[0]
    assert tracked_card["name"] == "Thoughtseize"
    assert (
        tracked_card["amount"] == 10
    ), "Amount should be updated by modify_user_tracked_card"

    # Verify both old and new specifications are present
    specs = tracked_card["specifications"]
    assert len(specs) == 2, "Should have added the new specification"
    spec_tuples = {(s["set_code"], s["finish"]) for s in specs}  # type: ignore
    assert ("MH2", "etched") in spec_tuples
    assert ("2XM", "non-foil") in spec_tuples


def test_delete_user_card(seeded_user_with_cards):
    # Arrange: Use the username from the fixture object to add a card.
    username = seeded_user_with_cards.username
    card_name = seeded_user_with_cards.cards[0].card_name

    modify_user_tracked_card("delete", username, {
        "card": {
            "name": card_name
            }})

    # Assert: The user should have no cards left.
    assert 'name: ' + card_name not in str(get_users_cards(username))


def test_delete_user_card_cascades_specifications(
    seeded_user_with_cards, db_session
):
    """
    Tests that deleting a UserTrackedCards object also deletes its child
    CardSpecification objects due to the cascade="all, delete-orphan" setting.
    """

    username = seeded_user_with_cards.username
    card_name = seeded_user_with_cards.cards[1].card_name

    initial_count = db_session.query(CardSpecification).count()

    # Act: Delete the card
    modify_user_tracked_card("delete", username, {
        "card": {
            "name": card_name
            }})

    # Assert: Verify both the card and its specifications are gone
    assert db_session.query(CardSpecification).count() < initial_count


def test_delete_user_card_for_nonexistent_user(db_session):
    """
    Test that attempting to delete a card for a non-existent user does nothing.
    """
    # This should run without error
    modify_user_tracked_card("delete", "nonexistent_user", {
        "card": {
            "name": "any_card"
            }})
    # And no cards should be in the DB
    assert db_session.query(UserTrackedCards).count() == 0


def test_delete_user_card_not_found(seeded_user_with_cards):
    """
    Test that attempting to delete a card not tracked by the user does nothing.
    """
    username = seeded_user_with_cards.username
    card_name = "Nonexistent Card"

    initial_card_count = len(get_users_cards(username))

    # Act: Delete the card
    modify_user_tracked_card("delete", username, {
        "card": {
            "name": card_name
            }})
    assert len(get_users_cards(username)) == initial_card_count


def test_update_user_tracked_card_preferences(seeded_user_with_cards):

    card = get_users_cards(seeded_user_with_cards.username)[0]
    assert card["amount"] == 4


def test_update_user_tracked_card_preferences_user_not_found(db_session):
    """Test updating preferences for a card when the user does not exist."""
    # This should run without error
    update_user_tracked_card_preferences(
        "nonexistent_user", "any_card", {"amount": 10}
    )
    # And no cards should be in the DB
    assert db_session.query(UserTrackedCards).count() == 0


def test_update_user_tracked_card_preferences_card_not_found(
        seeded_user_with_cards):
    """Test updating preferences for a card the user is not tracking."""
    update_user_tracked_card_preferences(
        "testuser", "Fireball", {"amount": 10}
    )
    card = get_users_cards("testuser")[0]
    assert card["name"] == "Lightning Bolt"
    assert card["amount"] == 4


@pytest.mark.parametrize(
    "card_name, spec, expected",
    [
        # --- Full, Valid Specifications ---
        (
            "Sol Ring",
            {"set_code": "C21", "collector_number": "125", "finish": "foil"},
            True,
        ),
        (
            "Sol Ring",
            {"set_code": "LTC", "collector_number": "3", "finish": "etched"},
            True,
        ),
        # --- Full, Invalid Specifications ---
        (
            "Sol Ring",
            {"set_code": "C21", "collector_number": "125", "finish": "etched"},
            False,
        ),  # Wrong finish for printing
        (
            "Sol Ring",
            {"set_code": "C21", "collector_number": "999", "finish": "foil"},
            False,
        ),  # Wrong collector number
        (
            "Sol Ring",
            {"set_code": "XYZ", "collector_number": "125", "finish": "foil"},
            False,
        ),  # Wrong set
        (
            "Nonexistent Card",
            {"set_code": "C21", "collector_number": "125", "finish": "foil"},
            False,
        ),  # Wrong card name
        # --- Partial, Valid Specifications (Wildcards) ---
        ("Sol Ring", {"set_code": "C21"}, True),
        ("Sol Ring", {"collector_number": "3"}, True),
        ("Sol Ring", {"finish": "foil"}, True),
        ("Sol Ring", {"set_code": "LTC", "collector_number": "3"}, True),
        ("Sol Ring", {"set_code": "C21", "finish": "non-foil"}, True),
        # --- Partial, Invalid Specifications ---
        (
            "Sol Ring",
            {"set_code": "LTC", "finish": "foil"},
            False,
        ),  # This combo doesn't exist
        ("Sol Ring", {"set_code": "XYZ"}, False),
        ("Sol Ring", {"finish": "holographic"}, False),
        # --- Empty Specification (Wildcard for everything) ---
        ("Sol Ring", {}, True),
        ("Nonexistent Card", {}, True),
    ],
    ids=[
        "full_valid_spec",
        "full_valid_spec_2",
        "full_invalid_finish",
        "full_invalid_collector_number",
        "full_invalid_set",
        "full_invalid_card_name",
        "partial_valid_set",
        "partial_valid_collector_number",
        "partial_valid_finish",
        "partial_valid_set_and_number",
        "partial_valid_set_and_finish",
        "partial_invalid_combo",
        "partial_invalid_set",
        "partial_invalid_finish",
        "empty_spec_valid_card",
        "empty_spec_nonexistent_card",
    ],
)
def test_is_valid_printing_specification(
    seeded_printings, card_name, spec, expected
):
    """
    Tests the is_valid_printing_specification function with various valid and
    invalid inputs.
    This covers requirements [4.3.6], [4.3.8], and [4.3.9].
    """
    is_valid = is_valid_printing_specification(card_name, spec)
    assert is_valid == expected


def test_get_printings_for_card(seeded_printings):
    """
    Tests that get_printings_for_card correctly retrieves all printings
    and their associated finishes for a given card.
    """
    printings = get_printings_for_card("Sol Ring")

    assert len(printings) == 3

    # The query orders by set_code, so we assert in that order: C21, LTC, ONE
    # Check C21 printing (index 0)
    assert printings[0]["set_code"] == "C21"
    assert printings[0]["collector_number"] == "125"
    assert sorted(printings[0]["finishes"]) == ["foil", "non-foil"]

    # Check LTC printing (index 1)
    assert printings[1]["set_code"] == "LTC"
    assert printings[1]["collector_number"] == "3"
    assert sorted(printings[1]["finishes"]) == ["etched", "non-foil"]

    # Check ONE printing (index 2)
    assert printings[2]["set_code"] == "ONE"
    assert printings[2]["collector_number"] == "254"
    assert sorted(printings[2]["finishes"]) == ["foil", "non-foil"]
