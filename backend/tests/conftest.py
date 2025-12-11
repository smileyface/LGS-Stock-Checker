import sys
import os

# Add the package root to the path to resolve module-level
# imports during test discovery.
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)


# Define a list of fixture modules to be loaded by pytest.
# This is the recommended way to make fixtures from other files available
# globally, and it avoids the issues associated with star imports.
pytest_plugins = [
    "tests.fixtures.app_fixtures",
    "tests.fixtures.db_fixtures",
    "tests.fixtures.mock_fixtures",
    "tests.fixtures.socket_fixtures",
    "tests.fixtures.cache_fixtures",
    "tests.fixtures.ws_fixtures",
]
