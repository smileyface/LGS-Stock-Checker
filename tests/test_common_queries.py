import pytest
from data.database.models.orm_models import User, Card, CardSpecification, UserTrackedCards
from werkzeug.security import generate_password_hash
from data.database.repositories.card_repository import get_users_cards


@pytest.fixture
def seeded_user_with_cards(db_session):
    """Fixture to create a user with multiple cards and specifications."""
    user = User(username="carduser", password_hash=generate_password_hash("password"))

    # Create the unique card names in the 'cards' lookup table first
    db_session.add_all([
        Card(name="Lightning Bolt"),
        Card(name="Counterspell"),
        Card(name="Sol Ring")
    ])
    # Commit to ensure these exist before we reference them via foreign key.
    db_session.commit()

    # Create the UserTrackedCards instances
    tracked_card1 = UserTrackedCards(card_name="Lightning Bolt", amount=4)
    tracked_card2 = UserTrackedCards(card_name="Counterspell", amount=2)
    tracked_card3 = UserTrackedCards(card_name="Sol Ring", amount=1)

    # Append specifications directly to the tracked card objects
    tracked_card1.specifications.append(CardSpecification(set_code="2ED", finish="non-foil"))
    tracked_card1.specifications.append(CardSpecification(set_code="3ED", finish="foil"))
    tracked_card2.specifications.append(CardSpecification(set_code="CMR", finish="etched"))

    # Append the fully-formed tracked cards to the user's collection
    user.cards.append(tracked_card1)
    user.cards.append(tracked_card2)
    user.cards.append(tracked_card3)

    # Add the top-level user object; cascades will handle the rest.
    db_session.add(user)
    db_session.commit()

    return user


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