import pytest
from unittest.mock import patch

@pytest.fixture(autouse=True)
def mock_socketio_context(mocker):
    """
    Mocks the 'emit' function from Flask-SocketIO to prevent actual
    network calls during tests. The necessary request/session context
    is provided by the 'app_context' fixture.
    """
    mocker.patch("managers.socket_manager.socket_emit.socketio.emit")

@pytest.fixture
def mock_store():
    """Mocks the store_manager.store_list function."""
    with patch("tasks.card_availability_tasks.store_manager") as mock:
        yield mock

@pytest.fixture
def mock_socket_emit():
    """Mocks the socket_emit.emit_from_worker function."""
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
    """Mocks the queue_task function used in the socket handlers."""
    return mocker.patch("managers.task_manager.queue_task")

@pytest.fixture
def mock_sh_get_current_user(mocker):
    """Mocks get_username and provides a default test user for socket handlers."""
    return mocker.patch("managers.socket_manager.socket_handlers.get_username", return_value="testuser")

@pytest.fixture
def mock_sh_emit(mocker):
    """Mocks the socketio.emit function used in the socket handlers."""
    return mocker.patch("managers.socket_manager.socket_handlers.socketio.emit")

@pytest.fixture
def mock_sh_trigger_availability_check(mocker):
    """Mocks the trigger_availability_check_for_card function used in socket handlers."""
    return mocker.patch("managers.socket_manager.socket_handlers.availability_manager.trigger_availability_check_for_card")