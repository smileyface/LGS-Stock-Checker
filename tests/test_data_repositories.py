import pytest
from werkzeug.security import generate_password_hash

import data
from data.database.models.orm_models import User, Store, Card, UserTrackedCards


@pytest.fixture
def seeded_user(db_session):
    """Fixture to create and commit a test user to the database."""
    user = User(username="testuser", password_hash=generate_password_hash("password"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def seeded_store(db_session):
    """Fixture to create and commit a test store to the database."""
    store = Store(
        name="Test Store",
        slug="test_store",
        homepage="https://test.com",
        search_url="https://test.com/search",
        fetch_strategy="default",
    )
    db_session.add(store)
    db_session.commit()
    db_session.refresh(store)
    return store


@pytest.fixture
def multiple_users_with_cards(db_session):
    """Fixture to create multiple users tracking various cards."""
    # Create unique card names
    cards = [Card(name="Sol Ring"), Card(name="Brainstorm"), Card(name="Lurrus of the Dream-Den")]
    db_session.add_all(cards)
    db_session.commit()

    # User 1 tracks Sol Ring and Brainstorm
    user1 = User(username="user1", password_hash="hash1")
    user1.cards.append(UserTrackedCards(card_name="Sol Ring", amount=1))
    user1.cards.append(UserTrackedCards(card_name="Brainstorm", amount=4))

    # User 2 tracks Sol Ring and Lurrus
    user2 = User(username="user2", password_hash="hash2")
    user2.cards.append(UserTrackedCards(card_name="Sol Ring", amount=1))
    user2.cards.append(UserTrackedCards(card_name="Lurrus of the Dream-Den", amount=1))

    # User 3 tracks no cards of interest
    user3 = User(username="user3", password_hash="hash3")

    db_session.add_all([user1, user2, user3])
    db_session.commit()

# --- User Repository Tests ---

def test_get_user_by_username(seeded_user):
    user = data.get_user_by_username("testuser")
    assert user is not None
    assert user.username == "testuser"
    assert data.get_user_by_username("nonexistent") is None


def test_add_user(db_session):
    """Test that a new user can be added to the database."""
    user = data.add_user("newuser", "newpasswordhash")
    assert user is not None
    assert user.username == "newuser"


def test_update_username(seeded_user):
    data.update_username("testuser", "updateduser")
    user = data.get_user_by_username("updateduser")
    assert user is not None
    assert user.username == "updateduser"
    assert data.get_user_by_username("testuser") is None


def test_update_password(seeded_user):
    new_hash = generate_password_hash("newpassword")
    data.update_password("testuser", new_hash)
    user = data.get_user_by_username("testuser")
    assert user.password_hash == new_hash


def test_user_store_preferences(seeded_user, seeded_store):
    # Initially, no stores are selected
    assert data.get_user_stores("testuser") == []

    # Add a store preference
    data.add_user_store("testuser", "test_store")
    stores = data.get_user_stores("testuser")
    assert len(stores) == 1
    assert stores[0].slug == "test_store"

    # Adding the same store again should not create a duplicate
    data.add_user_store("testuser", "test_store")
    assert len(data.get_user_stores("testuser")) == 1


def test_get_user_for_display(seeded_user):
    user = data.get_user_for_display("testuser")
    assert user is not None
    assert user.username == "testuser"
    # Ensure password hash is not present
    assert not hasattr(user, "password_hash")


def test_get_all_users(seeded_user):
    data.add_user("user2", "hash2")
    users = data.get_all_users()
    assert len(users) == 2
    assert "testuser" in [u.username for u in users]
    assert "user2" in [u.username for u in users]


# --- Card Repository Tests ---

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


def test_delete_user_card(seeded_user):
    data.add_user_card("testuser", "Lightning Bolt", 1, [])
    assert len(data.get_users_cards("testuser")) == 1

    data.delete_user_card("testuser", "Lightning Bolt")
    assert len(data.get_users_cards("testuser")) == 0


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


def test_update_user_tracked_card_preferences(seeded_user):
    data.add_user_card("testuser", "Swords to Plowshares", 1, [])
    data.update_user_tracked_card_preferences("testuser", "Swords to Plowshares", {"amount": 4})

    card = data.get_users_cards("testuser")[0]
    assert card.amount == 4


# --- Store Repository Tests ---

def test_get_store_metadata(seeded_store):
    store = data.get_store_metadata("test_store")
    assert store is not None
    assert store.name == "Test Store"


def test_get_all_stores(seeded_store):
    stores = data.get_all_stores()
    assert len(stores) >= 1
    assert "test_store" in [s.slug for s in stores]


# --- User-Card Query Tests ---

def test_get_users_tracking_card(multiple_users_with_cards):
    """Test finding all users who track a specific card."""
    # Sol Ring is tracked by user1 and user2
    users_tracking_sol_ring = data.get_users_tracking_card("Sol Ring")
    assert len(users_tracking_sol_ring) == 2
    usernames = {u.username for u in users_tracking_sol_ring}
    assert "user1" in usernames
    assert "user2" in usernames

    # Brainstorm is only tracked by user1
    users_tracking_brainstorm = data.get_users_tracking_card("Brainstorm")
    assert len(users_tracking_brainstorm) == 1
    assert users_tracking_brainstorm[0].username == "user1"

    # A card tracked by no one
    assert data.get_users_tracking_card("Black Lotus") == []


def test_get_tracking_users_for_cards(multiple_users_with_cards):
    """Test efficiently finding users for a list of cards."""
    card_names = ["Sol Ring", "Lurrus of the Dream-Den", "Black Lotus"]
    result = data.get_tracking_users_for_cards(card_names)

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
    assert data.get_tracking_users_for_cards([]) == {}