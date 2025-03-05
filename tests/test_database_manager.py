# tests/test_database_manager.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from managers.database_manager.tables import Base

# Override database connection for tests
TEST_DATABASE_URL = "sqlite:///:memory:"  # Use an in-memory database for testing
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Creates a fresh database schema before tests run."""
    Base.metadata.create_all(bind=test_engine)  # Create tables in test DB
    yield  # Run tests
    Base.metadata.drop_all(bind=test_engine)  # Drop tables after tests

@pytest.fixture(scope="function")
def db_session():
    """Provides a new database session for each test."""
    session = TestingSessionLocal()
    yield session
    session.rollback()  # Rollback any changes after each test
    session.close()

# Patch get_session to return the test session
@pytest.fixture(autouse=True)
def override_get_session(monkeypatch):
    monkeypatch.setattr("managers.database_manager.database_manager.get_session", lambda: TestingSessionLocal())
