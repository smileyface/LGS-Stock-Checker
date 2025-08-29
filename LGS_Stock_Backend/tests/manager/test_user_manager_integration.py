import pytest
from werkzeug.security import check_password_hash

from managers.user_manager import add_user, authenticate_user, get_user, update_username
from data.database.models.orm_models import User

# Note: We are NOT mocking the data layer here.
# These tests use the `db_session` fixture from conftest.py
# to interact with a real (in-memory) database, testing the full logic flow.


def test_add_user_integration_success(db_session):
    """
    GIVEN a valid username and password
    WHEN the add_user manager function is called
    THEN a new user should be created in the database with a hashed password.
    """
    username = "integration_user"
    password = "strong_password_123"

    # Act
    result = add_user(username, password)

    # Assert
    assert result is True

    # Verify directly in the database
    user_in_db = db_session.query(User).filter_by(username=username).one_or_none()
    assert user_in_db is not None
    assert user_in_db.username == username
    assert check_password_hash(user_in_db.password_hash, password)


def test_add_user_integration_already_exists(db_session):
    """
    GIVEN a username that already exists in the database
    WHEN the add_user manager function is called with that username
    THEN it should return False and not create a duplicate user.
    """
    # Arrange: create the initial user
    username = "existing_user"
    password = "password1"
    add_user(username, password)
    initial_user_count = db_session.query(User).count()

    # Act
    result = add_user(username, "some_other_password")

    # Assert
    assert result is False
    assert db_session.query(User).count() == initial_user_count


def test_authenticate_user_integration(db_session):
    """
    GIVEN a user created in the database
    WHEN the authenticate_user manager function is called
    THEN it should return True for correct credentials and False for incorrect ones.
    """
    # Arrange
    username = "auth_user"
    password = "auth_password"
    add_user(username, password)

    # Act & Assert
    assert authenticate_user(username, password) is True
    assert authenticate_user(username, "wrong_password") is False
    assert authenticate_user("non_existent_user", password) is False


def test_get_user_integration(db_session):
    """
    GIVEN a user created in the database
    WHEN the get_user manager function is called
    THEN it should return the correct user object or None.
    """
    # Arrange
    username = "get_user_test"
    password = "password"
    add_user(username, password)

    # Act & Assert
    user = get_user(username)
    assert user is not None
    assert user.username == username

    non_existent_user = get_user("non_existent_user")
    assert non_existent_user is None


def test_update_username_integration_success(db_session):
    """
    GIVEN a user in the database
    WHEN the update_username manager function is called with a new, unique username
    THEN it should return True and the username should be updated in the database.
    """
    # Arrange
    old_username = "old_name"
    new_username = "new_name"
    add_user(old_username, "password")

    # Act
    result = update_username(old_username, new_username)

    # Assert
    assert result is True
    user_in_db = db_session.query(User).filter_by(username=new_username).one_or_none()
    assert user_in_db is not None
    old_user_in_db = db_session.query(User).filter_by(username=old_username).one_or_none()
    assert old_user_in_db is None


def test_update_username_integration_name_taken(db_session):
    """
    GIVEN two users in the database
    WHEN update_username is called to change one user's name to the other's
    THEN it should return False and no changes should be made.
    """
    # Arrange
    user1_name = "user1"
    user2_name = "user2"
    add_user(user1_name, "pass1")
    add_user(user2_name, "pass2")

    # Act
    result = update_username(user1_name, user2_name)

    # Assert
    assert result is False
    user1_in_db = db_session.query(User).filter_by(username=user1_name).one_or_none()
    assert user1_in_db is not None  # user1 should still exist with old name