import pytest
from werkzeug.security import generate_password_hash

import data
from data.database.models.orm_models import User, Store


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