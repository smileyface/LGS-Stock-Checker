import pytest

import data
from data.database.models.orm_models import UserTrackedCards


def test_add_and_get_user_card(seeded_user):
    # Initially, no cards
    assert data.get_users_cards("testuser") == []

    # Add a card with specifications
    specs = [{"set_code": "ONE", "finish": "foil"}]
    data.add_user_card("testuser", "Sol Ring", 4, specs)

    cards = data.get_users_cards("testuser")
    assert len(cards) == 1
    assert cards[0].card_name == "Sol Ring"
    assert cards[0].amount == 4
    assert len(cards[0].specifications) == 1
    assert cards[0].specifications[0].set_code == "ONE"
    assert cards[0].specifications[0].finish == "foil"


def test_add_user_card_user_not_found(db_session):
    """Test that adding a card for a non-existent user does nothing."""
    data.add_user_card("nonexistent_user", "Some Card", 1, [])
    # Verify no UserTrackedCards were created
    assert db_session.query(UserTrackedCards).count() == 0


def test_add_user_card_for_existing_card_adds_specs_but_ignores_amount(seeded_user):
    """
    Test that calling add_user_card for a card that is already tracked:
    1. Adds new specifications.
    2. Does NOT create a duplicate card entry.
    3. Does NOT update the amount of the existing card.
    """
    # Arrange: Add the card initially with one spec and an amount of 1
    initial_specs = [{"set_code": "MH2", "finish": "etched"}]
    data.add_user_card("testuser", "Thoughtseize", 1, initial_specs)

    # Act: Call add_user_card again with a new spec and a DIFFERENT amount
    new_specs = [{"set_code": "2XM", "finish": "nonfoil"}]
    data.add_user_card("testuser", "Thoughtseize", 10, new_specs)

    # Assert
    cards = data.get_users_cards("testuser")
    assert len(cards) == 1, "Should not create a duplicate UserTrackedCards entry"

    tracked_card = cards[0]
    assert tracked_card.card_name == "Thoughtseize"
    assert tracked_card.amount == 1, "Amount should NOT be updated by add_user_card"

    # Verify both old and new specifications are present
    specs = tracked_card.specifications
    assert len(specs) == 2, "Should have added the new specification"
    spec_tuples = {(s.set_code, s.finish) for s in specs}
    assert ("MH2", "etched") in spec_tuples
    assert ("2XM", "nonfoil") in spec_tuples


def test_delete_user_card(seeded_user):
    data.add_user_card("testuser", "Lightning Bolt", 1, [])
    assert len(data.get_users_cards("testuser")) == 1

    data.delete_user_card("testuser", "Lightning Bolt")
    assert len(data.get_users_cards("testuser")) == 0


def test_delete_user_card_for_nonexistent_user(db_session):
    """Test that attempting to delete a card for a non-existent user does nothing."""
    # This should run without error
    data.delete_user_card("nonexistent_user", "any_card")
    # And no cards should be in the DB
    assert db_session.query(UserTrackedCards).count() == 0


def test_delete_user_card_not_found(seeded_user):
    """Test that attempting to delete a card not tracked by the user does nothing."""
    data.add_user_card("testuser", "Lightning Bolt", 1, [])
    initial_card_count = len(data.get_users_cards("testuser"))

    data.delete_user_card("testuser", "Fireball")  # This card is not tracked
    assert len(data.get_users_cards("testuser")) == initial_card_count


def test_update_user_tracked_cards_list(seeded_user):
    new_card_list = [
        {"card_name": "Brainstorm", "amount": 4},
        {"card_name": "Ponder", "amount": 4},
    ]
    data.update_user_tracked_cards_list("testuser", new_card_list)

    cards = data.get_users_cards("testuser")
    assert len(cards) == 2
    card_names = {c.card_name for c in cards}
    assert "Brainstorm" in card_names
    assert "Ponder" in card_names


def test_update_user_tracked_cards_list_clears_cards(seeded_user):
    """Test that passing an empty list removes all tracked cards for the user."""
    # Arrange: Add some cards first
    initial_list = [{"card_name": "Counterspell", "amount": 4}]
    data.update_user_tracked_cards_list("testuser", initial_list)
    assert len(data.get_users_cards("testuser")) == 1

    # Act & Assert: Update with an empty list and verify they are gone
    data.update_user_tracked_cards_list("testuser", [])
    assert len(data.get_users_cards("testuser")) == 0


def test_update_user_tracked_cards_list_for_nonexistent_user(db_session):
    """Test that updating the card list for a non-existent user does nothing."""
    card_list = [{"card_name": "Brainstorm", "amount": 4}]
    # This should run without error
    data.update_user_tracked_cards_list("nonexistent_user", card_list)
    # And no cards should be in the DB
    assert db_session.query(UserTrackedCards).count() == 0


def test_update_user_tracked_card_preferences(seeded_user):
    data.add_user_card("testuser", "Swords to Plowshares", 1, [])
    data.update_user_tracked_card_preferences("testuser", "Swords to Plowshares", {"amount": 4})

    card = data.get_users_cards("testuser")[0]
    assert card.amount == 4


def test_update_user_tracked_card_preferences_user_not_found(db_session):
    """Test updating preferences for a card when the user does not exist."""
    # This should run without error
    data.update_user_tracked_card_preferences("nonexistent_user", "any_card", {"amount": 10})
    # And no cards should be in the DB
    assert db_session.query(UserTrackedCards).count() == 0


def test_update_user_tracked_card_preferences_card_not_found(seeded_user):
    """Test updating preferences for a card the user is not tracking."""
    data.add_user_card("testuser", "Lightning Bolt", 1, [])
    data.update_user_tracked_card_preferences("testuser", "Fireball", {"amount": 10})
    card = data.get_users_cards("testuser")[0]
    assert card.card_name == "Lightning Bolt"
    assert card.amount == 1