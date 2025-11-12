import pytest
from run import create_app

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def app(mocker, db_session):
    """Creates a test Flask application instance for the entire test session."""
    # Define test-specific config overrides.
    # Using 'filesystem' for sessions avoids the need for a live Redis server during tests.
    test_config = {
        # Use the filesystem for sessions during tests to avoid needing a live Redis server.
        # This is crucial for isolated and fast unit/integration tests.
        "SESSION_TYPE": "filesystem",
        "TESTING": True,
        # Disable the message queue for tests to allow the Socket.IO test client to work.
        # The test client is not compatible with a message queue.
        "SOCKETIO_MESSAGE_QUEUE": None,
    }
    # Patch the worker listener to prevent the background thread from starting during tests.
    mocker.patch("managers.flask_manager.server_listener.start_server_listener")

    # Pass the overrides and the test database URL to the app factory.
    _app = create_app(
        "testing", override_config=test_config, database_url=TEST_DATABASE_URL
    )
    return _app


@pytest.fixture
def client(app):
    """A test client for the app."""
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def app_context(app):
    """Pushes a Flask application and request context for each test."""
    with app.test_request_context():
        from flask import request

        request.sid = "test_sid_12345"
        request.namespace = "/"
        yield
