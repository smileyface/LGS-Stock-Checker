import pytest
from flask import request
from app_factory import create_base_app, configure_web_app

TEST_DATABASE_URL = "sqlite:///:memory:"


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------
@pytest.fixture(scope="function")
def app(mocker, db_session):
    """
    Creates a test Flask application instance for the entire test session.
    Configured to use the filesystem for sessions (no Redis required).
    """
    test_config = {
        "SESSION_TYPE": "filesystem",
        "TESTING": True,
        "SOCKETIO_MESSAGE_QUEUE": None,  # Disable queue for testing
        "SOCKETIO_ASYNC_MODE": "threading",
    }

    # Patch the server listener to prevent background threads
    mocker.patch(
        "managers.messaging_manager.service_listener."
        "server_listener.start_server_listener"
    )

    # 1. Create base app
    _app = create_base_app(
        config_name="testing",
        override_config=test_config,
        database_url=TEST_DATABASE_URL,
    )
    # 2. Configure web layer
    _app = configure_web_app(_app)
    return _app


@pytest.fixture
def client(app):
    """Standard Flask test client."""
    with app.test_client() as client:
        yield client


@pytest.fixture
def auth_client(client, seeded_user):
    """
    A Flask test client that is already authenticated as 'seeded_user'.
    """
    # The password must match what the seeded_user fixture uses
    client.post(
        "/api/login", json={"username": seeded_user.username, "password": "password"}
    )
    return client


@pytest.fixture(autouse=True)
def mock_request_context(app):
    """
    Automatically pushes a request context for every test and mocks
    SocketIO specific attributes (sid, namespace).
    """
    with app.test_request_context():
        # Mock attributes usually provided by Flask-SocketIO during a request
        setattr(request, "sid", "test_sid_12345")
        setattr(request, "namespace", "/")
        yield


# Alias for backward compatibility if you prefer the old name
@pytest.fixture(autouse=True)
def app_context(mock_request_context):
    yield
