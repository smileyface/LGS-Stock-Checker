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
    # Define test-specific config overrides.
    # Using 'filesystem' for sessions avoids the need for a live Redis server during tests.
    test_config = {
        "SESSION_TYPE": "filesystem",
        "TESTING": True,
    }
    # Pass the overrides to the app factory.
    _app = create_app("testing", override_config=test_config)
    return _app


@pytest.fixture
def client(app):
    """A test client for the app."""
    with app.test_client() as client:
        yield client


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
        # Drop all tables to ensure a clean state for the next test.
        Base.metadata.drop_all(bind=db_config.engine)


@pytest.fixture
def seeded_user(db_session):
    """Fixture to create and commit a test user to the database."""
    user = User(username="testuser", password_hash=generate_password_hash("password"))
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def seeded_user_with_stores(db_session, seeded_user, seeded_stores):
    """Fixture to create a user and associate them with some stores."""
    # Re-fetch the user within the current session to ensure it's attached
    user = db_session.query(User).filter_by(username=seeded_user.username).one()
    user.selected_stores.extend(seeded_stores)
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
    # Patch the redis_conn object where it is *used* in the cache_manager module.
    # This is the most reliable way to ensure the mock is applied.
    mocker.patch("data.cache.cache_manager.redis_conn", mock_data_redis)

    mocker.patch("LGS_Stock_Backend.managers.redis_manager.redis_manager.redis_job_conn", mocker.MagicMock())
    # Mock the objects that capture the connection at import time
    # The mock for the queue needs a 'task' attribute to handle the @task decorator during test discovery.
    # This mock ensures that decorating a function with @queue.task just returns the original function.
    mock_queue = mocker.MagicMock()
    mock_queue.task.side_effect = lambda func: func
    mocker.patch("LGS_Stock_Backend.managers.redis_manager.redis_manager.queue", mock_queue)
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


@pytest.fixture(autouse=True)
def mock_fetch_scryfall_card_names(mocker):
    """Mocks the fetch_scryfall_card_names function."""
    # Patch the function where it is looked up (in the tasks module), not where it is defined.
    mock = mocker.patch("tasks.catalog_tasks.fetch_scryfall_card_names")
    mock.return_value = []  # Provide a safe, empty list as a default
    return mock


@pytest.fixture(autouse=True)
def mock_fetch_sets(mocker):
    """Mocks the fetch_all_sets function."""
    # Patch the function where it is looked up (in the tasks module).
    mock = mocker.patch("tasks.catalog_tasks.fetch_all_sets")
    mock.return_value = []  # Provide a safe, empty list as a default
    return mock


@pytest.fixture(autouse=True)
def mock_fetch_all_card_data(mocker):
    """Mocks the fetch_all_card_data function to prevent large network calls."""
    # Patch the function where it is looked up (in the tasks module).
    mock = mocker.patch("tasks.catalog_tasks.fetch_all_card_data")
    mock.return_value = []  # Provide a safe, empty list as a default
    return mock

@pytest.fixture
def mock_store():
    """Mocks the store_manager.store_list function."""
    with patch("tasks.card_availability_tasks.store_manager.store_list") as mock:
        yield mock

@pytest.fixture
def mock_cache_availability():
    """Mocks the availability_manager.cache_availability_data function."""
    with patch("tasks.card_availability_tasks.availability_manager.cache_availability_data") as mock:
        yield mock


@pytest.fixture
def mock_socket_emit():
    """Mocks the socket_emit.emit_from_worker function."""
    with patch("tasks.card_availability_tasks.socket_emit.emit_from_worker") as mock:
        yield mock