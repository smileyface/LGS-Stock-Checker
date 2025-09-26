import importlib
import inspect
import pkgutil
import warnings
import typing
from unittest.mock import MagicMock

import pytest
from werkzeug.security import generate_password_hash
from werkzeug.exceptions import HTTPException
from flask_socketio import SocketIO

from data.database.models.orm_models import Store, User
import managers, utility, data, routes, tasks


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


PACKAGES_TO_TEST = import_all_modules_from_packages(managers, data, utility, routes, tasks)


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
        pos_args = []
        kw_args = {}

        for param_name, param in params.items():
            arg_value = None
            is_kw_only = param.kind == inspect.Parameter.KEYWORD_ONLY

            # Use seeded data for common parameter names
            # Add a special case for `add_user` to avoid UNIQUE constraint violation
            if func.__name__ == 'add_user' and 'username' in param_name:
                arg_value = "new_smoke_test_user"
            elif "user" in param_name and ("name" in param_name or "username" in param_name):
                arg_value = live_user.username
            elif "user" in param_name and "id" in param_name:
                arg_value = live_user.id
            elif "store" in param_name and "id" in param_name:
                arg_value = live_store.id
            # Add a special case for the `set_user_stores` function, which expects a list of slugs.
            elif param_name == "store_slugs":
                arg_value = [live_store.slug]
            elif "slug" in param_name:
                arg_value = live_store.slug
            elif "password" in param_name and "hash" not in param_name:
                arg_value = "a_valid_password"
            elif "password_hash" in param_name:
                arg_value = "a_valid_test_hash"  # Provide a non-null hash
            elif "session" in param_name:  # The @db_query decorator injects the session
                # The test should not provide one, so we skip it.
                continue
            # Add specific handlers for common non-trivial types
            elif param.annotation is callable:
                arg_value = lambda: "dummy function"  # Provide a dummy callable
            elif param.annotation is SocketIO:
                arg_value = MagicMock()  # Provide a mock SocketIO object
            # Fallback to generic types
            else:
                origin = typing.get_origin(param.annotation)
                if param.default is not inspect.Parameter.empty:
                    arg_value = param.default
                elif hasattr(param.annotation, '__total__'):  # Heuristic for TypedDict
                    arg_value = {}
                elif param.annotation is dict or origin is dict:
                    arg_value = {}
                elif param.annotation is list or origin is list:
                    arg_value = []
                elif param.annotation == str:
                    arg_value = "test_string"
                elif param.annotation == int:
                    arg_value = 1  # Use a valid ID; 0 can be invalid
                elif param.annotation == bool:
                    arg_value = False
                else:
                    arg_value = None  # Safe fallback

            if is_kw_only:
                kw_args[param_name] = arg_value
            else:
                pos_args.append(arg_value)

        try:
            func(*pos_args, **kw_args)
        except HTTPException as e:
            # HTTP exceptions (like 401 Unauthorized or 404 Not Found) are expected outcomes
            # for route handlers when called without a proper request context.
            # We consider this a "pass" for a smoke test, as the function didn't crash
            # due to a programming error.
            pass
        except Exception as e:
            pytest.fail(
                f"Function {package.__name__}.{name}{inspect.signature(func)} "
                f"raised an exception with args {pos_args} and kwargs {kw_args}: {e}"
            )
