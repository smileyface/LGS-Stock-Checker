import sys
import os
from unittest.mock import MagicMock, patch

# Add the package root to the path to resolve module-level imports during test discovery.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import fixtures from the new modular structure.
# Pytest will automatically discover and use these fixtures.
from tests.fixtures.app_fixtures import *
from tests.fixtures.db_fixtures import *
from tests.fixtures.mock_fixtures import *
from tests.fixtures.socket_fixtures import *

# Import the helper function to set the global mock instance
from tests.fixtures.mock_fixtures import set_global_mock_redis_instance

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
    mock_redis_client_class.from_url.return_value = _global_mock_redis_instance # noqa
    mock_redis_client_class.return_value = _global_mock_redis_instance # noqa
    set_global_mock_redis_instance(_global_mock_redis_instance)

def pytest_unconfigure(config):
    """
    Called before test process is exited.
    """
    patch.stopall()
