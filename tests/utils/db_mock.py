# Force test database before any imports
import os
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from managers.database_manager.tables import Base

os.environ["DATABASE_URL"] = "postgresql://test_user:test_pass@localhost:5433/test_db"

# Mock database setup
TEST_DATABASE_URL = os.environ["DATABASE_URL"]
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=test_engine)

# Create tables in the test database before patching
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
setup_test_db()

# Properly override get_session to return a new session instance
def get_test_session():
    return TestingSessionLocal()

patch("managers.database_manager.database_manager.get_session", get_test_session).start()
patch("managers.database_manager.database_manager.engine", test_engine).start()
patch("managers.database_manager.database_manager.SessionLocal", TestingSessionLocal).start()