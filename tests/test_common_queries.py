import pytest
from managers.database_manager.tables import User
from managers.database_manager.common_queries import add_user, get_user_by_username

@pytest.mark.usefixtures("db_session")
def test_add_user(db_session):
    """Test inserting a user into the database."""
    user = add_user("testuser", "hashedpassword", session=db_session)

    assert user is not None
    assert user.username == "testuser"

@pytest.mark.usefixtures("db_session")
def test_get_user_by_username(db_session):
    """Test fetching a user by username."""
    add_user("testuser", "hashedpassword", session=db_session)
    user = get_user_by_username("testuser", session=db_session)

    assert user is not None
    assert user.username == "testuser"
