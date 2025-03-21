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
                print(f"✅ Successfully imported {module_name}")  # Green check emoji
            except (ImportError, redis.exceptions.ConnectionError) as e:
                if "redis" in str(e).lower():
                    warnings.warn(f"⚠️ Skipping {module_name} due to missing Redis dependency or connection error.")
                else:
                    raise e
    return modules


PACKAGES_TO_TEST = import_all_modules_from_packages(managers, core)


class TestAllFunctionsNoCrashes(unittest.TestCase):
    def test_all_functions_no_exceptions(self):
        for package in PACKAGES_TO_TEST:
            with self.subTest(package=package.__name__):
                for name, func in inspect.getmembers(package, inspect.isfunction):
                    params = inspect.signature(func).parameters

                    # Generate safe test inputs
                    args = []
                    for param_name, param in params.items():
                        if param.default is not inspect.Parameter.empty:
                            args.append(param.default)
                        elif param.annotation == str:
                            args.append("test")
                        elif param.annotation == int:
                            args.append(0)
                        elif param.annotation == list:
                            args.append([])
                        elif param.annotation == dict:
                            args.append({})
                        elif param.annotation == bool:
                            args.append(False)
                        else:
                            args.append(None)  # Safe fallback

                    try:
                        func(*args)
                    except Exception as e:
                        self.fail(f"Function {package.__name__}.{name} raised an exception: {e}")


if __name__ == "__main__":
    unittest.main()
