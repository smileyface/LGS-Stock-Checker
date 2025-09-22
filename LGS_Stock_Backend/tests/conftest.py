import sys
import os
import pytest
# Add the package root to the path to resolve module-level imports during test discovery.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Initialize the database with the test URL *before* any application modules are imported.
# This prevents the ImportError during test discovery.
from data.database import db_config
from data.database.models.orm_models import Base, User, Store
from flask import session
from unittest.mock import patch

TEST_DATABASE_URL = "sqlite:///:memory:"

from werkzeug.security import generate_password_hash
from run import create_app


@pytest.fixture(scope="session")
def app():
    """Creates a test Flask application instance for the entire test session."""
    _app = create_app("testing")
    return _app


@pytest.fixture(autouse=True)
def app_context(app):
    """
    Pushes a Flask application and request context for each test.
    This makes 'app', 'g', 'request', and 'session' available and mocks
    request attributes needed by SocketIO handlers.
    """
    with app.test_request_context():
        # Add 'sid' to the request object for SocketIO handlers
        from flask import request
        request.sid = "test_sid_12345"
        request.namespace = "/"  # Add the default namespace for SocketIO handlers
        yield


@pytest.fixture(scope="function")
def db_session():
    """
    Pytest fixture that provides a clean, isolated database session for each test function.
    It handles the full lifecycle: initializing the test database, creating tables,
    yielding a session, and tearing everything down.
    """
    # Initialize the database for testing. The `initialize_database` function
    # is idempotent (it checks if the engine is already set), so this is safe
    # to call for every test. This also ensures that tests which do not use
    # the database do not incur the overhead of initializing it.
    db_config.initialize_database(TEST_DATABASE_URL, for_testing=True)

    # Create tables before the test runs
    Base.metadata.create_all(bind=db_config.engine)
    session_instance = db_config.SessionLocal()
    try:
        # Yield the actual SQLAlchemy session instance to the tests.
        yield session_instance
    finally:
        # Use .remove() to be consistent with the @db_query decorator's cleanup.
        # This ensures the session is properly disposed from the scoped_session registry.
        db_config.SessionLocal.remove()
        Base.metadata.drop_all(bind=db_config.engine)  # Drop tables after the test


@pytest.fixture
def seeded_user(db_session):
    """Fixture to create and commit a test user to the database."""
    user = User(username="testuser", password_hash=generate_password_hash("password"))
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def seeded_stores(db_session):
    """Fixture to create and commit multiple test stores to the database."""
    stores_data = [
        Store(
            name="Test Store",
            slug="test_store",
            homepage="https://test.com",
            search_url="https://test.com/search",
            fetch_strategy="default",
        ),
        Store(
            name="Another Store",
            slug="another_store",
            homepage="https://another.com",
            search_url="https://another.com/search",
            fetch_strategy="default",
        ),
    ]
    db_session.add_all(stores_data)
    db_session.commit()
    return stores_data


@pytest.fixture
def seeded_store(seeded_stores):
    """Fixture to provide a single test store from the list of seeded stores."""
    return next(s for s in seeded_stores if s.slug == "test_store")


@pytest.fixture(autouse=True)
def mock_redis(mocker):
    """
    Automatically mock the low-level Redis connection objects and the
    import-time Queue/Scheduler objects to prevent any real network calls.
    """
    # Mock the data layer's redis connection with configured return values
    mock_data_redis = mocker.MagicMock()
    mock_data_redis.get.return_value = None  # Simulate key not found
    mock_data_redis.hgetall.return_value = {}  # Simulate empty hash
    mocker.patch("LGS_Stock_Backend.data.redis_client.redis_conn", mock_data_redis)

    mocker.patch("LGS_Stock_Backend.managers.redis_manager.redis_manager.redis_job_conn", mocker.MagicMock())
    # Mock the objects that capture the connection at import time
    mocker.patch("LGS_Stock_Backend.managers.redis_manager.redis_manager.queue", mocker.MagicMock())
    mocker.patch("LGS_Stock_Backend.managers.redis_manager.redis_manager.scheduler", mocker.MagicMock())


@pytest.fixture(autouse=True)
def mock_socketio_context(mocker):
    """
    Mocks the 'emit' function from Flask-SocketIO to prevent actual
    network calls during tests. The necessary request/session context
    is provided by the 'app_context' fixture.
    """
    # Mock the main socketio object's emit function to prevent network calls
    mocker.patch("LGS_Stock_Backend.managers.socket_manager.socket_emit.socketio.emit")
    # Mock the SocketIO class itself within socket_emit to handle the worker case
    mocker.patch("LGS_Stock_Backend.managers.socket_manager.socket_emit.SocketIO")
