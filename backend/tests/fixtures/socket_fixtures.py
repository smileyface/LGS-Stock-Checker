import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def mock_socketio_emit(mocker):
    """
    Global Mock: Patches the canonical source of socketio.emit.

    This ensures that ANY module importing 'socketio' from
    'managers.socket_manager.socket_manager' uses this same mock.
    """
    return mocker.patch("managers.socket_manager.socket_manager.socketio.emit")


@pytest.fixture
def mock_sh_emit(mock_socketio_emit):
    """
    Provides the global socket mock to specific tests that request it.

    This replaces the old approach of re-patching the specific file import,
    which caused the 'Called 0 times' error because the test was asserting
    on Mock A while the code was calling Mock B (or the real function).
    """
    return mock_socketio_emit


# -----------------------------------------------------------------------------
# Other Handlers & Helpers
# -----------------------------------------------------------------------------

@pytest.fixture
def mock_store():
    """Mocks the store_manager used in tasks."""
    with patch("tasks.card_availability_tasks.store_manager") as mock:
        yield mock


@pytest.fixture
def mock_socket_emit_worker():
    """
    Mocks emit_from_worker.
    (Renamed from mock_socket_emit to avoid confusion with the main socket mock)
    """
    with patch("tasks.card_availability_tasks.socket_emit.emit_from_worker") as mock:
        yield mock


@pytest.fixture
def mock_sh_user_manager(mocker):
    """Mocks the user_manager used in the socket handlers."""
    return mocker.patch("managers.socket_manager.socket_handlers.user_manager")


@pytest.fixture
def mock_sh_database(mocker):
    """Mocks the database module used in the socket handlers."""
    return mocker.patch("managers.socket_manager.socket_handlers.database")


@pytest.fixture
def mock_sh_queue_task(mocker):
    """Mocks the queue_task function."""
    return mocker.patch("managers.task_manager.queue_task")


@pytest.fixture
def mock_sh_get_current_user(mocker):
    """
    Mocks get_username.
    Defaults to 'testuser' so tests don't fail on authentication checks.
    """
    return mocker.patch(
        "managers.socket_manager.socket_handlers.get_username",
        return_value="testuser",
    )


@pytest.fixture
def logged_in_user(mock_sh_get_current_user):
    """
    Semantic fixture: explicitly states 'I need a logged-in user context'.
    """
    class User:
        username = "testuser"
    return User()


@pytest.fixture
def mock_sh_trigger_availability_check(mocker):
    """Mocks the availability manager trigger."""
    return mocker.patch(
        "managers.socket_manager.socket_handlers."
        "availability_manager.trigger_availability_check_for_card"
    )
