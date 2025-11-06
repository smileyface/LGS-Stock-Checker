import pytest
from unittest.mock import MagicMock, patch

from data.database.session_manager import db_query
from data.database.models.orm_models import User

@pytest.fixture(autouse=True)
def stop_global_db_mock(mocker):
    """Stop the global mock of get_session to allow local patching in this module."""
    mocker.stopall()
    yield

# The path to SessionLocal where it's looked up. The db_query decorator in
# session_manager imports `db_config` and then calls `db_config.get_session()`
# and `db_config.SessionLocal`, so we must patch it there.
SESSION_LOCAL_PATH = "data.database.session_manager.SessionLocal"


def test_db_query_success():
    """
    Tests that the db_query decorator commits the session and returns the result
    when the wrapped function executes successfully.
    """
    # 1. Arrange
    mock_session = MagicMock()
    # Create a mock that looks like a SQLAlchemy ORM object
    mock_orm_object = User(username="test", password_hash="test")

    # Patch the SessionLocal factory to control session creation
    with patch(SESSION_LOCAL_PATH, return_value=mock_session) as mock_session_local_factory:

        @db_query
        def successful_function(arg1, session=None):
            # The decorator should inject the session
            assert session is not None
            session.add(arg1)
            return "Success"

        # 2. Act
        result = successful_function(mock_orm_object)

        # 3. Assert
        # Check session management
        mock_session_local_factory.assert_called_once()  # Session was created from the factory
        mock_session.commit.assert_called_once()  # Transaction was committed
        mock_session.rollback.assert_not_called()  # Rollback was not called
        mock_session_local_factory.remove.assert_called_once()  # Session was closed/removed

        # Check function behavior
        mock_session.add.assert_called_once_with(mock_orm_object)
        assert result == "Success"


def test_db_query_exception_rolls_back_and_reraises():
    """
    Tests that the db_query decorator rolls back the session and re-raises the exception
    when the wrapped function fails.
    """
    # 1. Arrange
    mock_session = MagicMock()
    mock_orm_object = User(username="test", password_hash="test")
    test_exception = ValueError("Something went wrong") # noqa

    with patch(SESSION_LOCAL_PATH, return_value=mock_session) as mock_session_local_factory:

        @db_query # noqa
        def failing_function(session=None):
            session.add(mock_orm_object)
            raise test_exception
            
        # 2. Act & Assert
        with pytest.raises(ValueError) as excinfo:
            failing_function()
            
        # Check that the original exception was re-raised
        assert excinfo.value is test_exception

        # Check session management
        mock_session_local_factory.assert_called_once()
        mock_session.commit.assert_not_called()  # Commit was not called
        mock_session.rollback.assert_called_once()  # Rollback was called
        mock_session_local_factory.remove.assert_called_once()  # Session was still closed

        # Check function behavior
        mock_session.add.assert_called_once_with(mock_orm_object)


def test_db_query_passes_args_and_kwargs():
    """
    Tests that the db_query decorator correctly passes positional and keyword
    arguments to the wrapped function.
    """
    # 1. Arrange
    mock_session = MagicMock()

    with patch(SESSION_LOCAL_PATH, return_value=mock_session) as mock_session_local_factory:

        @db_query
        def function_with_args(arg1, kwarg1=None, session=None):
            # Return the received arguments to verify them
            return {
                "arg1": arg1,
                "kwarg1": kwarg1,
                "session_received": session is mock_session,
            }

        # 2. Act
        result = function_with_args("pos1", kwarg1="key1")

        # 3. Assert
        mock_session_local_factory.remove.assert_called_once()
        mock_session.commit.assert_called_once()

        expected = {"arg1": "pos1", "kwarg1": "key1", "session_received": True}
        assert result == expected