# Force test database before any imports
import os
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from managers.database_manager.tables import Base

os.environ["DATABASE_URL"] = "postgresql://test_user:test_pass@192.168.1.120:5435/test_db"


# Mock database setup
TEST_DATABASE_URL = os.environ["DATABASE_URL"]
if "sqlite" in TEST_DATABASE_URL:
    test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    test_engine = create_engine(TEST_DATABASE_URL)  # No `check_same_thread` for PostgreSQL
TestingSessionLocal = sessionmaker(bind=test_engine)


# Create tables in the test database before patching
def setup_test_db():
    """Resets the test database schema before tests."""
    Base.metadata.drop_all(bind=test_engine)  # ✅ Wipe existing tables
    Base.metadata.create_all(bind=test_engine)


setup_test_db()


# Properly override get_session to return a new session instance
def get_test_session():
    return TestingSessionLocal()

