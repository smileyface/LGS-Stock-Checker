import pytest
from data.database.models.orm_models import (
    User,
    Card,
    CardSpecification,
    UserTrackedCards,
)
from werkzeug.security import generate_password_hash
from data.database.repositories.card_repository import get_users_cards
from data.database.repositories.user_repository import (
    get_users_tracking_card,
    get_tracking_users_for_cards,
)


@pytest.fixture
def seeded_user_with_cards(db_session):
    """Fixture to create a user with multiple cards and specifications."""
    user = User(
        username="carduser", password_hash=generate_password_hash("password")
    )

    # Create the unique card names in the 'cards' lookup table first
    db_session.add_all(
        [
            Card(name="Lightning Bolt"),
            Card(name="Counterspell"),
            Card(name="Sol Ring"),
        ]
    )
    # Commit to ensure these exist before we reference them via foreign key.
    db_session.commit()

    # Create the UserTrackedCards instances
    tracked_card1 = UserTrackedCards(card_name="Lightning Bolt", amount=4)
    tracked_card2 = UserTrackedCards(card_name="Counterspell", amount=2)
    tracked_card3 = UserTrackedCards(card_name="Sol Ring", amount=1)

    # Append specifications directly to the tracked card objects
    tracked_card1.specifications.append(
        CardSpecification(set_code="2ED", finish="non-foil")
    )
    tracked_card1.specifications.append(
        CardSpecification(set_code="3ED", finish="foil")
    )
    tracked_card2.specifications.append(
        CardSpecification(set_code="CMR", finish="etched")
    )

    # Append the fully-formed tracked cards to the user's collection
    user.cards.append(tracked_card1)
    user.cards.append(tracked_card2)
    user.cards.append(tracked_card3)

    # Add the top-level user object; cascades will handle the rest.
    db_session.add(user)
    db_session.commit()

    return user


@pytest.fixture
def multiple_users_with_cards(db_session):
    """Fixture to create multiple users tracking various cards."""
    # Create unique card names
    cards = [
        Card(name="Sol Ring"),
        Card(name="Brainstorm"),
        Card(name="Lurrus of the Dream-Den"),
    ]
    db_session.add_all(cards)
    db_session.commit()

    # User 1 tracks Sol Ring and Brainstorm
    user1 = User(username="user1", password_hash="hash1")
    user1.cards.append(UserTrackedCards(card_name="Sol Ring", amount=1))
    user1.cards.append(UserTrackedCards(card_name="Brainstorm", amount=4))

    # User 2 tracks Sol Ring and Lurrus
    user2 = User(username="user2", password_hash="hash2")
    user2.cards.append(UserTrackedCards(card_name="Sol Ring", amount=1))
    user2.cards.append(
        UserTrackedCards(card_name="Lurrus of the Dream-Den", amount=1)
    )

    # User 3 tracks no cards of interest
    user3 = User(username="user3", password_hash="hash3")

    db_session.add_all([user1, user2, user3])
    db_session.commit()


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
    assert cards_data[0].specifications[0].finish == "etched"

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
