import pytest
from werkzeug.security import generate_password_hash

from managers.database_manager.common_queries import (
    get_user_by_username, update_username, update_password,
    get_users_cards, update_user_tracked_cards_list,
    get_cards_by_name, get_all_cards, get_store_metadata, get_all_stores
)
from managers.database_manager.tables import User, Store
from tests.utils.db_mock import get_test_session


@pytest.fixture(scope="function")
def db_session():
    session = get_test_session()
    yield session
    session.rollback()
    session.close()


def test_user_queries(db_session):
    """Tests user-related queries."""
    # Insert a mock user
    test_user = User(username="testuser", password_hash=generate_password_hash("password"))
    db_session.add(test_user)
    db_session.commit()

    # Get user by username
    user = get_user_by_username("testuser")
    assert user.username == "testuser"

    # Update username
    update_username("testuser", "newtestuser")
    user = get_user_by_username("newtestuser")
    assert user.username == "newtestuser"

    # Update password
    update_password("newtestuser", generate_password_hash("newpassword"))
    user = get_user_by_username("newtestuser")
    assert user.password_hash != test_user.password_hash  # Ensure password is updated


def test_store_queries(db_session):
    """Tests store-related queries."""
    # Insert a mock store
    test_store = Store(id=1, name="Test Store", slug="test-store", homepage="https://test.com",
                       search_url="https://test.com/search", fetch_strategy="default")
    db_session.add(test_store)
    db_session.commit()

    # Get store metadata
    store_metadata = get_store_metadata("test-store")
    assert store_metadata["name"] == "Test Store"

    # Get all stores
    stores = get_all_stores()
    assert len(stores) > 0


def test_card_queries(db_session):
    """Tests card-related queries."""
    # Insert a user and cards
    test_user = User(username="testuser", password_hash=generate_password_hash("password"))
    db_session.add(test_user)
    db_session.commit()

    card_list = [{"card_name": "Lightning Bolt"}, {"card_name": "Counterspell"}]
    update_user_tracked_cards_list("testuser", card_list)

    # Get user cards
    cards = get_users_cards("testuser")
    assert len(cards) == 2

    # Get cards by name (raw SQL)
    retrieved_cards = get_cards_by_name("Lightning Bolt")
    assert len(retrieved_cards) > 0

    # Get all cards
    all_cards = get_all_cards()
    assert len(all_cards) > 0
