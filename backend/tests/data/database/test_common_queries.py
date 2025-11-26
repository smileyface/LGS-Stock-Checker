import pytest  # noqa

from data.database.repositories.card_repository import (
    get_users_cards,
    add_card_to_user,
    update_user_tracked_card_preferences
)
from data.database.repositories.user_repository import (
    get_users_tracking_card,
    get_tracking_users_for_cards,
)


def test_get_users_cards(seeded_user_with_cards):
    """
    Tests the get_users_cards function to ensure it
    returns cards with their associated specifications correctly.
    """
    username = seeded_user_with_cards.username
    cards_data = get_users_cards(username)

    assert len(cards_data) == 3

    # Sort cards by name to make assertions deterministic
    cards_data.sort(key=lambda c: c.card_name)

    # Assertions for Counterspell
    assert cards_data[0].card_name == "Counterspell"
    assert cards_data[0].amount == 2
    assert len(cards_data[0].specifications) == 1
    assert cards_data[0].specifications[0].set_code == "CMR"
    assert cards_data[0].specifications[0].finish.name == "etched"

    # Assertions for Lightning Bolt
    assert cards_data[1].card_name == "Lightning Bolt"
    assert cards_data[1].amount == 4
    assert len(cards_data[1].specifications) == 2
    spec_sets = {s.set_code for s in cards_data[1].specifications}
    assert "2ED" in spec_sets
    assert "3ED" in spec_sets

    # Assertions for Sol Ring
    assert cards_data[2].card_name == "Sol Ring"
    assert cards_data[2].amount == 1
    assert len(cards_data[2].specifications) == 0


def test_get_users_cards_no_cards(seeded_user):
    """
    Tests that get_users_cards returns an empty list for a user who exists
    but is not tracking any cards.
    """
    username = seeded_user.username
    cards_data = get_users_cards(username)
    assert cards_data == []


def test_get_users_cards_user_not_found(db_session):
    """
    Tests that get_users_cards returns an empty list when the user
    does not exist in the database.
    """
    cards_data = get_users_cards("non_existent_user")
    assert cards_data == []


def test_get_users_tracking_card(multiple_users_with_cards):
    """Test finding all users who track a specific card."""
    # Sol Ring is tracked by user1 and user2
    users_tracking_sol_ring = get_users_tracking_card("Sol Ring")
    assert len(users_tracking_sol_ring) == 2
    usernames = {u.username for u in users_tracking_sol_ring}
    assert "user1" in usernames
    assert "user2" in usernames

    # Brainstorm is only tracked by user1
    users_tracking_brainstorm = get_users_tracking_card("Brainstorm")
    assert len(users_tracking_brainstorm) == 1
    assert users_tracking_brainstorm[0].username == "user1"

    # A card tracked by no one
    assert get_users_tracking_card("Black Lotus") == []


def test_get_tracking_users_for_cards(multiple_users_with_cards):
    """Test efficiently finding users for a list of cards."""
    card_names = ["Sol Ring", "Lurrus of the Dream-Den", "Black Lotus"]
    result = get_tracking_users_for_cards(card_names)

    # Check Sol Ring
    assert "Sol Ring" in result
    sol_ring_users = result["Sol Ring"]
    assert len(sol_ring_users) == 2
    sol_ring_usernames = {u.username for u in sol_ring_users}
    assert "user1" in sol_ring_usernames
    assert "user2" in sol_ring_usernames

    # Check Lurrus
    assert "Lurrus of the Dream-Den" in result
    assert len(result["Lurrus of the Dream-Den"]) == 1
    assert result["Lurrus of the Dream-Den"][0].username == "user2"

    # Check Black Lotus (tracked by no one)
    assert "Black Lotus" in result
    assert result["Black Lotus"] == []

    # Check empty input
    assert get_tracking_users_for_cards([]) == {}


def test_add_new_card_to_user_with_existing_cards(seeded_user_with_cards):
    """
    Tests adding a completely new card to a user who is already tracking
    other cards.
    """
    username = seeded_user_with_cards.username

    # Define a new card to add
    new_card_data = {
        "card_name": "Brainstorm",
        "amount": 3,
        "specifications": [{"set_code": "ICE", "finish": "non-foil"}],
    }

    # Act: Add the new card to the user
    add_card_to_user(username,
                     new_card_data)

    # Assert: Verify the card was added and existing cards are untouched
    all_cards = get_users_cards(username)
    assert len(all_cards) == 4  # 3 existing + 1 new

    # Find the newly added card
    added_card = next(
        (c for c in all_cards if c.card_name == "Brainstorm"), None
    )

    assert added_card is not None
    assert added_card.amount == 3
    assert len(added_card.specifications) == 1
    assert added_card.specifications[0].set_code == "ICE"


@pytest.mark.parametrize(
        "card_data",
        [
            {
                "card_name": "Sol Ring",
                "update_data": {"amount": 5},
                "expected_amount": 5,
                "expected_specs_count": 0,
            },
            {
                "card_name": "Sol Ring",
                "update_data": {
                    "specifications": [{"set_code": "LTC", "finish": "etched"}]
                },
                "expected_amount": 1,  # Original amount
                "expected_specs_count": 1,
            },
            {
                "card_name": "Lightning Bolt",
                "update_data": {
                    "specifications": [{"set_code": "4ED", "finish": "non-foil"}]
                },
                "expected_amount": 4,  # Original amount
                "expected_specs_count": 1,
                "expected_set_code": "4ED",
            },
        ],
)
def test_update_user_card(seeded_user_with_cards, card_data):
    """
    Tests updating a user's tracked card, including amount and specifications.
    """
    username = seeded_user_with_cards.username
    card_name = card_data["card_name"]
    update_data = card_data["update_data"]

    # Act: Update the card
    update_user_tracked_card_preferences(
        username, card_name, update_data
    )

    # Assert: Verify the update
    all_cards = get_users_cards(username)
    updated_card = next((c for c in all_cards if c.card_name == card_name), None)

    assert updated_card is not None
    assert updated_card.amount == card_data["expected_amount"]
    assert len(updated_card.specifications) == card_data["expected_specs_count"]

    # If we updated specs, let's check them
    if "expected_set_code" in card_data:
        assert updated_card.specifications[0].set_code == card_data["expected_set_code"]
