import pytest
from tests.utils.db_mock import get_test_session
from managers.user_manager import (
    user_exists, get_user, add_user, update_username,
    authenticate_user, update_selected_stores, get_selected_stores,
    load_card_list, save_card_list
)
from managers.database_manager.tables import User
from werkzeug.security import generate_password_hash
from sqlalchemy.orm import scoped_session, sessionmaker

@pytest.fixture(scope="function")
def db_session():
    session_factory = sessionmaker(bind=get_test_session().bind)
    session = scoped_session(session_factory)
    yield session
    session.rollback()
    session.remove()

def test_user_manager_package(db_session):
    """Tests the package as a black box using the actual database structure."""
    # Insert a mock user into the test database with hashed password
    test_user = User(username="testuser", password_hash=generate_password_hash("password"))
    db_session.add(test_user)
    db_session.commit()

    # Authentication
    assert authenticate_user("testuser", "password")  # 🔹 Should work now

    # User retrieval
    user = get_user("testuser")
    assert user["username"] == "testuser"

    # User creation
    assert add_user("newuser", "password")

    # Username update
    update_username("testuser", "newtestuser")
    user = get_user("newtestuser")
    assert user["username"] == "newtestuser"

    # Card management
    assert load_card_list("testuser") == []  # No cards inserted yet
    assert save_card_list("testuser", [{"card_name": "Lightning Bolt"}])
    assert load_card_list("testuser") == [{"card_name": "Lightning Bolt"}]

    # Store preferences
    assert get_selected_stores("testuser") == []
