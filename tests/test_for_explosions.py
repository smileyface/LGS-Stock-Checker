import unittest
import importlib
import inspect
import pkgutil
import warnings
import redis.exceptions


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


import managers, core  # Example: Import multiple packages
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
