import importlib
import inspect
import pkgutil
import unittest
import warnings

import redis.exceptions

from managers.database_manager.tables import Store
from tests.utils.db_mock import *
from tests.utils.redis_mock import *


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
                print(f"✅ Successfully imported {module_name}", flush=True)  # Green check emoji
            except (ImportError, redis.exceptions.ConnectionError) as e:
                if "redis" in str(e).lower():
                    warnings.warn(f"⚠️ Skipping {module_name} due to missing Redis dependency or connection error.")
                else:
                    raise e
    return modules


PACKAGES_TO_TEST = import_all_modules_from_packages(managers, core)


class TestAllFunctionsImport(unittest.TestCase):
    packages = managers, core
    def test_all_functions_import_no_exceptions(self):
        for package in self.packages:
            for _, module_name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
                try:
                    module = importlib.import_module(module_name)
                    self.assertTrue(True, f"{module_name} successfully loaded")
                except (ImportError, redis.exceptions.ConnectionError) as e:
                    if "redis" in str(e).lower():
                        warnings.warn(f"⚠️ Skipping {module_name} due to missing Redis dependency or connection error.")
                    else:
                        self.fail(f"{module_name} failed loading")

if __name__ == "__main__":
    unittest.main()
