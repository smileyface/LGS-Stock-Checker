from data.database.models.orm_models import (
    UserTrackedCards,
    CardSpecification,
    Finish
)
from data.database.repositories.card_repository import (
    get_users_cards,
    modify_user_tracked_card,
    update_user_tracked_card_preferences
)
from data.database.repositories.user_repository import (
    get_users_tracking_card,
)


def test_get_users_cards(db_session, user_factory, printing_factory):
    """
    Tests that we can retrieve cards with complex specifications.
    Refactored to build its own specific data scenario.
    """
    # 1. Arrange: Create the Catalog Data (The "Global" state)
    # We need specific finishes and sets to exist for our specifications
    printing_factory(card_name="Lightning Bolt", set_code="2ED", finishes=["non-foil"])
    printing_factory(card_name="Lightning Bolt", set_code="3ED", finishes=["non-foil"])
    printing_factory(card_name="Counterspell", set_code="CMR", finishes=["etched"])
    printing_factory(card_name="Sol Ring")  # Generic

    # 2. Arrange: Create the User
    user = user_factory(username="collector_steve")

    # 3. Arrange: Give the User some tracked cards
    # Helper to get IDs quickly
    get_finish_id = lambda name: db_session.query(Finish).filter_by(name=name).one().id

    # Card 1: Lightning Bolt (4 copies, 2 specific versions)
    bolt = UserTrackedCards(card_name="Lightning Bolt", amount=4)
    bolt.specifications.append(CardSpecification(
        set_code="2ED", finish_id=get_finish_id("non-foil")
    ))
    bolt.specifications.append(CardSpecification(
        set_code="3ED", finish_id=get_finish_id("non-foil")
    ))

    # Card 2: Counterspell (2 copies, etched)
    cspell = UserTrackedCards(card_name="Counterspell", amount=2)
    cspell.specifications.append(CardSpecification(
        set_code="CMR", finish_id=get_finish_id("etched")
    ))

    # Card 3: Sol Ring (1 copy, no specs)
    sol = UserTrackedCards(card_name="Sol Ring", amount=1)

    user.cards.extend([bolt, cspell, sol])
    db_session.commit()

    # 4. Act
    cards_data = get_users_cards("collector_steve")

    # 5. Assert
    assert len(cards_data) == 3

    # Verify Lightning Bolt
    bolt_data = next(c for c in cards_data if c.card.name == "Lightning Bolt")
    assert bolt_data.amount == 4
    assert len(bolt_data.specifications) == 2
    codes = {s.set_code for s in bolt_data.specifications}
    assert codes == {"2ED", "3ED"}


def test_get_users_cards_empty(user_factory):
    """Simple test for a user with no cards."""
    user_factory(username="empty_user")
    assert get_users_cards("empty_user") is None


def test_get_users_tracking_card(db_session, user_factory, card_factory):
    """
    Test finding all users who track a specific card.
    """
    # 1. Arrange: Create Catalog
    card_factory(name="Sol Ring")
    card_factory(name="Brainstorm")

    # 2. Arrange: Create Users and track cards
    # User 1 tracks both
    user1 = user_factory(username="alice")
    user1.cards.append(UserTrackedCards(card_name="Sol Ring", amount=1))
    user1.cards.append(UserTrackedCards(card_name="Brainstorm", amount=4))

    # User 2 tracks only Sol Ring
    user2 = user_factory(username="bob")
    user2.cards.append(UserTrackedCards(card_name="Sol Ring", amount=1))

    db_session.commit()

    # 3. Act & Assert
    # Sol Ring (Both)
    users_sol = get_users_tracking_card("Sol Ring")
    assert len(users_sol) == 2
    assert {"alice", "bob"} == {u.username for u in users_sol}

    # Brainstorm (Alice only)
    users_bs = get_users_tracking_card("Brainstorm")
    assert len(users_bs) == 1
    assert users_bs[0].username == "alice"

    # Black Lotus (No one)
    assert get_users_tracking_card("Black Lotus") == []


def test_add_new_card_to_user_integration(db_session, user_factory, printing_factory):
    """
    Tests the repository function for adding a new card.
    """
    # 1. Arrange: Setup catalog for the card we want to add
    printing_factory(card_name="Brainstorm", set_code="ICE", finishes=["non-foil"])

    user_factory(username="testuser")

    # 2. Act
    new_card_payload = {
        "card_name": "Brainstorm",
        "amount": 3,
        "specifications": [
            {"set_code": {"code": "ICE"}, "finish": {"name": "non-foil"}}
        ],
    }
    modify_user_tracked_card("add", "testuser", new_card_payload)

    # 3. Assert
    # Re-fetch user from DB to see if relation exists
    # (We can use the repo function itself to verify)
    cards = get_users_cards("testuser")
    assert len(cards) == 1
    assert cards[0].card_name == "Brainstorm"
    assert cards[0].specifications[0].set_code == "ICE"


def test_update_user_card_specs(db_session, user_factory, printing_factory):
    """
    Tests updating a specification.
    """
    # 1. Arrange: User tracks a normal Sol Ring
    printing_factory(card_name="Sol Ring", set_code="C21", finishes=["etched"])

    user = user_factory(username="updater")
    tracked = UserTrackedCards(card_name="Sol Ring", amount=1)
    user.cards.append(tracked)
    db_session.commit()

    # 2. Act: Add a specification to the existing card
    update_data = {
        "specifications": [
            {"set_code": {"code": "C21"}, "finish": {"name": "etched"}}
        ]
    }
    update_user_tracked_card_preferences("updater", "Sol Ring", update_data)

    # 3. Assert
    cards = get_users_cards("updater")
    assert len(cards) == 1
    assert cards[0].specifications[0].finish.name == "etched"
