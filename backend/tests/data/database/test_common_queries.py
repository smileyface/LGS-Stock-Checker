import pytest  # noqa

from data.database.repositories.card_repository import get_users_cards
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
