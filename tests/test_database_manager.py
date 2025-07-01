# tests/test_database_manager.py
import pytest
from sqlalchemy.orm.session import Session
from data.database.db_config import get_session


# This file previously contained database setup fixtures that have now been
# centralized into tests/conftest.py to be used across the entire test suite.
# You can add specific tests for the database manager here if needed.

def test_get_session(db_session):
    """Verify that get_session returns a valid session object."""
    session = get_session()
    assert isinstance(session, Session)
    session.close()

    # Test that the session is closed when the test function ends
def test_get_session_is_scoped(db_session):
    """
    Verify that get_session returns a session from the scoped_session,
    meaning it's the same session within the same thread/context.
    """
    session1 = get_session()
    session2 = get_session()
    assert session1 is session2
    session1.close() # Closing one should not affect the other if they are the same
