import sys
import os
import pytest
import redis # Import redis here for global patching
from unittest.mock import MagicMock, patch
# Add the package root to the path to resolve module-level imports during test discovery.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import models for use in fixtures. Database modules will be imported within fixtures
# to ensure they are configured for the test environment.
from data.database.models.orm_models import Base, User, Store, Card, Set, Finish, CardPrinting
from flask import session
from unittest.mock import patch
TEST_DATABASE_URL = "sqlite:///:memory:"

from werkzeug.security import generate_password_hash
from run import create_app

# Global variables to hold the patcher and the mock Redis instance
_global_redis_patcher = None
_global_mock_redis_instance = None

def pytest_configure(config):
    """
    Called after command line options have been parsed and plugins have been loaded.
    This is the earliest point to patch modules that are imported during test collection.
    """
    global _global_redis_patcher, _global_mock_redis_instance

    # Create a mock instance that will be returned by all calls to Redis() or Redis.from_url()
    _global_mock_redis_instance = MagicMock()

    # Use create_autospec to create a mock *class* that mimics the real redis.Redis class.
    # This is crucial for `isinstance()` checks to work correctly in third-party libraries.
    mock_redis_client_class = patch("redis.Redis", autospec=True).start()
    mock_redis_client_class.from_url.return_value = _global_mock_redis_instance
    mock_redis_client_class.return_value = _global_mock_redis_instance

    # We no longer need a global patcher variable to manage start/stop manually here.
    # The patch is started and we can let pytest handle cleanup.

def pytest_unconfigure(config):
    """
    Called before test process is exited.
    """
    global _global_redis_patcher
    patch.stopall()

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
    mocker.patch("managers.flask_manager.worker_listener.start_worker_listener")

    # Pass the overrides and the test database URL to the app factory.
    _app = create_app("testing", override_config=test_config, database_url=TEST_DATABASE_URL)
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
    Provides a clean, isolated database session for each test function.
    This fixture now handles the entire database lifecycle: creating the engine,
    creating tables, yielding a session, and tearing everything down.
    """
    from data.database import db_config, session_manager

    # Initialize the database with the test URL for this specific test run.
    db_config.initialize_database(TEST_DATABASE_URL)
    engine = db_config.get_engine()
    Base.metadata.create_all(bind=engine)
    
    session_instance = session_manager.get_session()
    try:
        yield session_instance
    finally:
        # Ensure the session is removed before dropping tables.
        session_manager.remove_session()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
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
def mock_redis_manager_objects(mocker):
    """
    Automatically mock the low-level Redis connection objects and the
    import-time Queue/Scheduler objects to prevent any real network calls.
    """
    global _global_mock_redis_instance # Access the globally stored mock instance

    # Ensure redis_job_conn points to our global mock instance.
    # This handles cases where redis_manager was imported before the global patch fully took effect on its module-level variable.
    mocker.patch("LGS_Stock_Backend.managers.redis_manager.redis_manager.redis_job_conn", _global_mock_redis_instance)

    # Mock the objects that capture the connection at import time
    # The mock for the queue needs a 'task' attribute to handle the @task decorator during test discovery.
    # This mock ensures that decorating a function with @queue.task just returns the original function.
    mock_queue = mocker.MagicMock()
    mock_queue.task.side_effect = lambda func: func
    mocker.patch("LGS_Stock_Backend.managers.redis_manager.redis_manager.queue", mock_queue)
    mocker.patch("LGS_Stock_Backend.managers.redis_manager.redis_manager.scheduler", mocker.MagicMock())
    
    # Explicitly patch data.cache.cache_manager.redis_conn if it's a separate module-level instance.
    # This ensures it also uses the globally mocked Redis.
    mocker.patch("data.cache.cache_manager.redis_conn", _global_mock_redis_instance)


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
def mock_fetch_sets(mocker):
    """Mocks the fetch_all_sets function."""
    # Patch the function where it is defined.
    mock = mocker.patch("externals.scryfall_api.fetch_all_sets")
    mock.return_value = []  # Provide a safe, empty list as a default
    return mock


@pytest.fixture(autouse=True)
def mock_fetch_all_card_data(mocker):
    """Mocks the fetch_all_card_data function to prevent large network calls."""
    # Patch the function where it is defined.
    mock = mocker.patch("externals.scryfall_api.fetch_all_card_data")
    mock.return_value = []  # Provide a safe, empty list as a default
    return mock

@pytest.fixture
def mock_store():
    """Mocks the store_manager.store_list function."""
    with patch("tasks.card_availability_tasks.store_manager.store_list") as mock:
        yield mock


@pytest.fixture
def mock_socket_emit():
    """Mocks the socket_emit.emit_from_worker function."""
    with patch("tasks.card_availability_tasks.socket_emit.emit_from_worker") as mock:
        yield mock


# --- Fixtures for Socket Handlers ---

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
    """
    Mocks the queue_task function used in the socket handlers.
    The target is where the function is *looked up*.
    """
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

@pytest.fixture
def mock_cache_availability(mocker):
    """Mocks the cache_availability function used in socket handlers."""
    return mocker.patch("managers.availability_manager.cache_availability_data")


@pytest.fixture
def seeded_printings(db_session):
    """Fixture to create a card with multiple printings and finishes."""
    # Seed lookup tables
    db_session.add_all([
        Card(name="Sol Ring"),
        Card(name="Thoughtseize"),
        Card(name="Ugin, the Spirit Dragon"),
        Set(code="C21", name="Commander 2021"),
        Set(code="LTC", name="The Lord of the Rings: Tales of Middle-earth Commander"),
        Set(code="ONE", name="Phyrexia: All Will Be One"),
        Set(code="MH2", name="Modern Horizons 2"),
        Set(code="2XM", name="Double Masters"),
        Set(code="M21", name="Core Set 2021"),
        Finish(name="nonfoil"),
        Finish(name="foil"),
        Finish(name="etched")
    ])
    db_session.commit()

    # Create printings and associate finishes
    printings_data = [
        ("Sol Ring", "C21", "125", ["nonfoil", "foil"]),
        ("Sol Ring", "LTC", "3", ["nonfoil", "etched"]),
        ("Sol Ring", "ONE", "254", ["nonfoil", "foil"]),
        ("Thoughtseize", "MH2", "107", ["etched"]),
        ("Thoughtseize", "2XM", "107", ["nonfoil"]),
        ("Ugin, the Spirit Dragon", "M21", "1", ["foil"]),
    ]

    all_finishes = {f.name: f for f in db_session.query(Finish).all()}

    for card_name, set_code, collector_number, finish_names in printings_data:
        printing = CardPrinting(card_name=card_name, set_code=set_code, collector_number=collector_number)
        printing.available_finishes.extend([all_finishes[name] for name in finish_names])
        db_session.add(printing)

    db_session.commit()