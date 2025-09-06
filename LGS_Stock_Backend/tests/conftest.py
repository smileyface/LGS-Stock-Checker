import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from werkzeug.security import generate_password_hash

from run import create_app
from data.database.models.orm_models import Base, User, Store
 # Use an in-memory SQLite database for fast, isolated tests
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
# Use a scoped_session to mimic the application's session management
# expire_on_commit=False is crucial for tests where objects created in one
# transaction need to be accessed after that transaction's session is closed.
TestingSessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False))


@pytest.fixture(scope="session")
def app():
    """Creates a test Flask application instance for the entire test session."""
    _app = create_app("testing")
    return _app


@pytest.fixture(autouse=True)
def app_context(app):
    """
    Pushes a Flask application and request context for each test.
    This makes 'app', 'g', 'request', and 'session' available.
    It also pre-populates the request and session with test data needed
    by the SocketIO handlers.
    """
    with app.test_request_context():
        # Add 'sid' to the request object for SocketIO handlers
        from flask import request
        request.sid = "test_sid_12345"
        request.namespace = "/"  # Add the default namespace for SocketIO handlers

        # Populate the session with a test user
        from flask import session
        session['username'] = 'testuser'

        yield


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
    Mocks the 'emit' function from Flask-SocketIO to prevent actual
    network calls during tests. The necessary request/session context
    is provided by the 'app_context' fixture.
    """
    # Mock the main socketio object's emit function to prevent network calls
    mocker.patch("managers.socket_manager.socket_emit.socketio.emit")
    # Mock the SocketIO class itself within socket_emit to handle the worker case
    mocker.patch("managers.socket_manager.socket_emit.SocketIO")


@pytest.fixture(autouse=True)
def mock_template_rendering(mocker):
    """
    Automatically mocks Flask's `render_template` function to prevent
    TemplateNotFound errors in tests that call route functions.
    This isolates route tests to their Python logic, not UI rendering.
    """
    # Patch where the function is looked up (in each route module that uses it).
    mocker.patch("routes.home_routes.render_template", return_value="<mocked_template>")
    mocker.patch("routes.user_routes.render_template", return_value="<mocked_template>")