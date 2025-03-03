import unittest
import importlib
import inspect
import pkgutil
import warnings
import os
from unittest.mock import MagicMock, patch
import redis.exceptions
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from managers.database_manager.tables import Base, Store

# Force test database before any imports
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# Mock Redis globally before importing any modules
mock_redis = MagicMock()
patch("redis.Redis", return_value=mock_redis).start()
patch("rq_scheduler.Scheduler", return_value=mock_redis).start()
patch("managers.redis_manager.redis_manager.redis_conn", new=mock_redis).start()

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

# Insert mock store data
def seed_test_store():
    session = get_test_session()
    try:
        test_store = Store(
            id=1,
            name="Authority Games Mesa, AZ",
            slug="authority_games_mesa_az",
            homepage="https://authoritygames.com",
            search_url="https://authoritygames.com/search",
            fetch_strategy="default",
        )
        session.add(test_store)
        session.commit()
    finally:
        session.close()

seed_test_store()

# Import managers only after database override
import managers, core  # Example: Import multiple packages

def import_all_modules_from_packages(*packages):
    """Dynamically imports all submodules from multiple packages and prints successful imports."""
    modules = []
    for package in packages:
        for _, module_name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
            try:
                module = importlib.import_module(module_name)
                modules.append(module)
                print(f"✅ Successfully imported {module_name}")  # Green check emoji
            except (ImportError, redis.exceptions.ConnectionError) as e:
                if "redis" in str(e).lower():
                    warnings.warn(f"⚠️ Skipping {module_name} due to missing Redis dependency or connection error.")
                else:
                    raise e
    return modules

PACKAGES_TO_TEST = import_all_modules_from_packages(managers, core)

class TestAllPackagesExceptions(unittest.TestCase):
    def test_all_functions_no_exceptions(self):
        for package in PACKAGES_TO_TEST:
            with self.subTest(package=package.__name__):
                for name, func in inspect.getmembers(package, inspect.isfunction):
                    try:
                        params = inspect.signature(func).parameters
                        args = [None] * len(params)  # Provide dummy arguments
                        func(*args)
                    except Exception as e:
                        self.fail(f"Function {package.__name__}.{name} raised an exception: {e}")

if __name__ == "__main__":
    unittest.main()