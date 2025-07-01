import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from data.database.models.orm_models import Base

# Use an in-memory SQLite database for fast, isolated tests
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
# Use a scoped_session to mimic the application's session management
TestingSessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))


@pytest.fixture(scope="function")
def db_session():
    """
    Pytest fixture to provide a clean database session for each test function.
    Creates all tables, yields a session, and then drops all tables.
    """
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


# This fixture is crucial for tests that call application code
# which in turn tries to get a database session.
@pytest.fixture(autouse=True)
def override_get_session(monkeypatch):
    """
    Patch the session factory *where it is used* (in the session_manager).
    This ensures that the @db_query decorator uses the in-memory test database.
    """
    monkeypatch.setattr("data.database.session_manager.SessionLocal", TestingSessionLocal)


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
    mocker.patch("data.redis_client.redis_conn", mock_data_redis)

    mocker.patch("managers.redis_manager.redis_manager.redis_job_conn", mocker.MagicMock())
    # Mock the objects that capture the connection at import time
    mocker.patch("managers.redis_manager.redis_manager.queue", mocker.MagicMock())
    mocker.patch("managers.redis_manager.redis_manager.scheduler", mocker.MagicMock())


@pytest.fixture(autouse=True)
def mock_socketio_context(mocker):
    """
    Mocks Flask-SocketIO context objects like 'request' and 'session'
    to prevent 'Working outside of request context' errors. It also mocks
    the 'emit' function to prevent actual network calls during tests.
    """
    mock_request = mocker.MagicMock()
    mock_request.sid = "test_sid_12345"
    mocker.patch("managers.socket_manager.socket_connections.request", mock_request, create=True)
    mocker.patch("managers.socket_manager.socket_handlers.request", mock_request, create=True)

    # Mock the session object to provide a default username
    mock_session = mocker.MagicMock()
    mock_session.get.return_value = "testuser"
    mocker.patch("managers.socket_manager.socket_handlers.session", mock_session, create=True)

    # Patch the 'emit' function where it is *used* to ensure the mock is effective,
    mocker.patch("managers.socket_manager.socket_events.emit", create=True)
    mocker.patch("managers.socket_manager.socket_emit.emit", create=True)