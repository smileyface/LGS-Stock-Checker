import importlib
import inspect
import pkgutil
import warnings
import typing
from unittest.mock import MagicMock

import pytest
from werkzeug.security import generate_password_hash
from flask_socketio import SocketIO

from LGS_Stock_Backend.data.database.models.orm_models import Store, User
from LGS_Stock_Backend import managers, utility, data, routes


def import_all_modules_from_packages(*packages):
    """Dynamically imports all submodules from multiple packages and prints successful imports."""
    modules = []
    for package in packages:
        for _, module_name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
            try:
                module = importlib.import_module(module_name)
                modules.append(module)
                # print(f"✅ Successfully imported {module_name}")
            except ImportError as e:
                warnings.warn(f"⚠️ Failed to import {module_name}: {e}")
    return modules


PACKAGES_TO_TEST = import_all_modules_from_packages(managers, data, utility, routes)


@pytest.fixture
def seed_data(db_session):
    """Seeds the database with a test user and a test store for smoke tests."""
    test_user = User(id=1, username="testuser", password_hash=generate_password_hash("password"))
    test_store = Store(
        id=1,
        name="Test Store",
        slug="test_store",
        homepage="https://test.com",
        search_url="https://test.com/search",
        fetch_strategy="default",
    )
    db_session.add(test_user)
    db_session.add(test_store)
    db_session.commit()
    # Return the IDs of the created objects. This avoids passing detached
    # instances to the test function, which can cause errors.
    return {"user_id": test_user.id, "store_id": test_store.id}


@pytest.mark.smoke
@pytest.mark.parametrize("package", PACKAGES_TO_TEST, ids=[p.__name__ for p in PACKAGES_TO_TEST])
def test_all_functions_no_crashes(package, seed_data, db_session, mocker):
    """
    Smoke test to ensure that functions can be called with basic, safe inputs
    without raising exceptions. This test uses seeded data for more realistic scenarios.
    """
    # Mock the underlying get_json method to prevent crashes in route handlers
    # that access request.json without the correct Content-Type header.
    mocker.patch("werkzeug.wrappers.request.Request.get_json", return_value={})

    for name, func in inspect.getmembers(package, inspect.isfunction):
        # Ensure we only test functions defined in the current package, not imported ones.
        if func.__module__ != package.__name__:
            continue

        # Because repository functions create and destroy their own sessions via the
        # @db_query decorator, the original `seed_data` objects can become detached.
        # We re-fetch them inside the loop using the main test session (`db_session`)
        # to ensure we have "live" objects for generating arguments.
        live_user = db_session.query(User).filter_by(id=seed_data["user_id"]).one()
        live_store = db_session.query(Store).filter_by(id=seed_data["store_id"]).one()

        params = inspect.signature(func).parameters

        # Generate safe test inputs
        args = []
        for param_name, param in params.items():
            # Use seeded data for common parameter names
            # Add a special case for `add_user` to avoid UNIQUE constraint violation
            if func.__name__ == 'add_user' and 'username' in param_name:
                args.append("new_smoke_test_user")
                continue

            if "user" in param_name and ("name" in param_name or "username" in param_name):
                args.append(live_user.username)
                continue
            elif "user" in param_name and "id" in param_name:
                args.append(live_user.id)
                continue
            elif "store" in param_name and "id" in param_name:
                args.append(live_store.id)
                continue
            elif "slug" in param_name:
                args.append(live_store.slug)
                continue
            elif "password" in param_name and "hash" not in param_name:
                args.append("a_valid_password")
                continue
            elif "password_hash" in param_name:
                args.append("a_valid_test_hash")  # Provide a non-null hash
                continue
            elif "session" in param_name:  # The @db_query decorator injects the session
                # The test should not provide one, so we skip it.
                continue
            # Add specific handlers for common non-trivial types
            elif param.annotation is callable:
                args.append(lambda: "dummy function")  # Provide a dummy callable
                continue
            elif param.annotation is SocketIO:
                args.append(MagicMock())  # Provide a mock SocketIO object
                continue
            # Fallback to generic types
            origin = typing.get_origin(param.annotation)
            if param.default is not inspect.Parameter.empty:
                args.append(param.default)
            elif hasattr(param.annotation, '__total__'):  # Heuristic for TypedDict
                args.append({})
            elif param.annotation is dict or origin is dict:
                args.append({})
            elif param.annotation is list or origin is list:
                args.append([])
            elif param.annotation == str:
                args.append("test_string")
            elif param.annotation == int:
                args.append(1)  # Use a valid ID; 0 can be invalid
            elif param.annotation == bool:
                args.append(False)
            else:
                args.append(None)  # Safe fallback

        try:
            func(*args)
        except Exception as e:
            pytest.fail(
                f"Function {package.__name__}.{name}{inspect.signature(func)} "
                f"raised an exception with args {args}: {e}"
            )
