import pytest
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError

import data
from data.database.models.orm_models import User


@pytest.mark.parametrize(
    "username, should_find_user",
    [
        ("testuser", True),      # Case: User exists
        ("nonexistent", False),  # Case: User does not exist
        ("TestUser", False),     # Case: Check case-sensitivity (assuming it should be exact)
    ],
)
def test_get_user_by_username(seeded_user, username, should_find_user):
    """
    GIVEN a seeded user in the database
    WHEN get_user_by_username is called with various usernames
    THEN the function returns a user object for an existing user and None otherwise.
    """
    # Act
    user = data.get_user_by_username(username)
    if should_find_user:
        assert user is not None
        assert user.username == username
    else:
        assert user is None


def test_add_user(db_session):
    """
    GIVEN an empty database session
    WHEN add_user is called with a new username and password hash
    THEN a new user is created in the database and returned.
    """
    # Act
    user = data.add_user("newuser", "newpasswordhash")

    # Assert
    assert user is not None
    assert user.username == "newuser"


def test_add_user_already_exists(seeded_user):
    """
    GIVEN a user with a specific username already exists
    WHEN add_user is called with the same username
    THEN an IntegrityError is raised.
    """
    # Act & Assert
    with pytest.raises(IntegrityError):
        data.add_user("testuser", "some_other_hash")


def test_update_username(seeded_user):
    """
    GIVEN a user exists in the database
    WHEN update_username is called with a new username
    THEN the user's username is updated, and the old username is no longer found.
    """
    # Act
    data.update_username("testuser", "updateduser")

    # Assert
    user = data.get_user_by_username("updateduser")
    assert user is not None
    assert user.username == "updateduser"
    assert data.get_user_by_username("testuser") is None


def test_update_username_user_not_found(db_session):
    """
    GIVEN no user exists in the database
    WHEN update_username is called for a non-existent user
    THEN the function completes without error and no user is created.
    """
    # Act
    data.update_username("nonexistent_user", "new_username")

    # Assert
    assert data.get_user_by_username("new_username") is None


def test_update_password(seeded_user):
    """
    GIVEN a user exists in the database
    WHEN update_password is called with a new password hash
    THEN the user's password_hash is updated in the database.
    """
    # Act
    new_hash = generate_password_hash("newpassword")
    data.update_password("testuser", new_hash)

    # Assert
    user = data.get_user_by_username("testuser")
    assert user.password_hash == new_hash


def test_update_password_user_not_found(db_session):
    """
    GIVEN no user exists in the database
    WHEN update_password is called for a non-existent user
    THEN the function completes without error and no user is created.
    """
    # Act
    data.update_password("nonexistent_user", "new_hash")

    # Assert
    assert data.get_user_by_username("nonexistent_user") is None


def test_user_store_preferences(seeded_user, seeded_store):
    """
    GIVEN a user and store exist in the database
    WHEN user store preferences are added
    THEN the preferences are saved, and duplicates or non-existent stores are ignored.
    """
    # Assert initial state
    assert data.get_user_stores("testuser") == []

    # Act: Add a store preference
    data.add_user_store("testuser", "test_store")

    # Assert: Store is added
    stores = data.get_user_stores("testuser")
    assert len(stores) == 1
    assert stores[0].slug == "test_store"

    # Act: Add the same store again
    data.add_user_store("testuser", "test_store")

    # Assert: No duplicate is created
    assert len(data.get_user_stores("testuser")) == 1

    # Act: Attempt to add a non-existent store
    initial_store_count = len(data.get_user_stores("testuser"))
    data.add_user_store("testuser", "non_existent_store")

    # Assert: Count remains unchanged
    assert len(data.get_user_stores("testuser")) == initial_store_count


def test_remove_user_store_preference(seeded_user, seeded_store):
    """
    GIVEN a user has a saved store preference
    WHEN remove_user_store is called for that preference
    THEN the preference is removed from the database.
    """
    # Arrange
    data.add_user_store("testuser", "test_store")
    assert len(data.get_user_stores("testuser")) == 1

    # Act: Remove the preference
    data.remove_user_store("testuser", "test_store")

    # Assert: The preference should be gone
    assert len(data.get_user_stores("testuser")) == 0


def test_get_user_stores_user_not_found(db_session):
    """
    GIVEN no user exists in the database
    WHEN get_user_stores is called for a non-existent user
    THEN an empty list is returned.
    """
    # Act
    stores = data.get_user_stores("nonexistent_user")

    # Assert
    assert stores == []


def test_get_user_for_display(seeded_user):
    """
    GIVEN a user exists in the database
    WHEN get_user_for_display is called
    THEN a user object is returned without the password_hash attribute.
    """
    # Act
    user = data.get_user_for_display("testuser")

    # Assert
    assert user is not None
    assert user.username == "testuser"
    assert not hasattr(user, "password_hash")


def test_get_user_for_display_not_found(db_session):
    """
    GIVEN no user exists in the database
    WHEN get_user_for_display is called for a non-existent user
    THEN None is returned.
    """
    # Act
    user = data.get_user_for_display("nonexistent_user")

    # Assert
    assert user is None


def test_get_all_users(seeded_user):
    """
    GIVEN multiple users exist in the database
    WHEN get_all_users is called
    THEN a list of all user objects is returned.
    """
    # Arrange
    data.add_user("user2", "hash2")

    # Act
    users = data.get_all_users()

    # Assert
    assert len(users) == 2
    assert "testuser" in [u.username for u in users]
    assert "user2" in [u.username for u in users]


def test_get_all_users_empty(db_session):
    """
    GIVEN the database is empty
    WHEN get_all_users is called
    THEN an empty list is returned.
    """
    # Act
    users = data.get_all_users()

    # Assert
    assert users == []