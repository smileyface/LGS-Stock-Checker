import pytest
from werkzeug.security import generate_password_hash

from data.database.models.orm_models import User
from managers.user_manager import (
    get_user, add_user, update_username,
    authenticate_user, get_selected_stores,
    load_card_list, save_card_list
)

@pytest.fixture
def seeded_user(db_session):
    """Fixture to create and commit a test user to the database."""
    test_user = User(username="testuser", password_hash=generate_password_hash("password"))
    db_session.add(test_user)
    db_session.commit()
    # Refresh the instance to prevent DetachedInstanceError
    db_session.refresh(test_user)
    return test_user

def test_user_manager_package(db_session, seeded_user):
    """Tests the user manager functions using a pre-seeded user."""
    original_username = "testuser"

    # Authentication
    assert authenticate_user(original_username, "password")

    # User retrieval
    user = get_user(original_username)
    assert user.username == original_username

    # User creation
    assert add_user("newuser", "password")

    # Username update
    update_username(original_username, "newtestuser")
    user = get_user("newtestuser")
    assert user.username == "newtestuser"

    # Card management
    assert load_card_list("newtestuser") == []  # No cards inserted yet
    assert save_card_list("newtestuser", [{"card_name": "Lightning Bolt", "amount": 1}])

    # Verify the saved card by checking the object's attributes
    card_list = load_card_list("newtestuser")
    assert len(card_list) == 1
    assert card_list[0].card_name == "Lightning Bolt"

    # Store preferences
    assert get_selected_stores("newtestuser") == []
