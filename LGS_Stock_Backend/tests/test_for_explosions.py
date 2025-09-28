import importlib
import inspect
import pkgutil
import warnings
import typing
from unittest.mock import MagicMock

from datetime import datetime
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


def _generate_test_args(func, params, live_user, live_store):
    """
    Generates positional and keyword arguments for a function based on its signature,
    using seeded data and safe defaults.
    """
    pos_args = []
    kw_args = {}

    # A mapping for functions that expect a specific 'data' payload.
    data_payloads = {
        "handle_get_card_printings": {"card_name": "test_card"},
        "handle_add_user_tracked_card": {"card": "test_card", "amount": 1, "card_specs": {}},
        "handle_delete_user_tracked_card": {"card": "test_card"},
        "handle_update_user_tracked_cards": {"card": "test_card", "update_data": {"amount": 2}},
        "handle_update_user_stores": {"stores": ["test_store"]},
    }

    for param_name, param in params.items():
        arg_value = None
        is_kw_only = param.kind == inspect.Parameter.KEYWORD_ONLY

        # --- Argument Generation Logic ---
        # 1. Handle specific, known parameter names and function contexts.
        if func.__name__ == 'add_user' and 'username' in param_name:
            arg_value = "new_smoke_test_user"
        elif param_name == "data" and func.__name__ in data_payloads:
            arg_value = data_payloads[func.__name__]
        elif "user" in param_name and ("name" in param_name or "username" in param_name):
            arg_value = live_user.username
        elif "user" in param_name and "id" in param_name:
            arg_value = live_user.id
        elif "store" in param_name and "id" in param_name:
            arg_value = live_store.id
        elif param_name == "store_slugs":
            arg_value = [live_store.slug]
        elif "slug" in param_name:
            arg_value = live_store.slug
        elif "password" in param_name and "hash" not in param_name:
            arg_value = "a_valid_password"
        elif "password_hash" in param_name:
            arg_value = "a_valid_test_hash"
        elif "session" in param_name:
            continue  # The @db_query decorator injects the session; skip.

        # 2. Handle common non-trivial types.
        elif param.annotation is callable:
            arg_value = lambda: "dummy function"
        elif param.annotation is SocketIO:
            arg_value = MagicMock()

        # 3. Fallback to generic types based on type hints or defaults.
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
                arg_value = 1
            elif param.annotation == float:
                arg_value = 1.0
            elif param.annotation == datetime:
                arg_value = datetime.now()
            elif param.annotation == bool:
                arg_value = False
            else:
                arg_value = None  # Safe fallback

        if is_kw_only:
            kw_args[param_name] = arg_value
        else:
            pos_args.append(arg_value)

    return pos_args, kw_args


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

    # Fetch seeded objects once per module test, not once per function.
    # This significantly reduces redundant database queries.
    live_user = db_session.query(User).filter_by(id=seed_data["user_id"]).one()
    live_store = db_session.query(Store).filter_by(id=seed_data["store_id"]).one()

    for name, func in inspect.getmembers(package, inspect.isfunction):
        # Ensure we only test functions defined in the current package, not imported ones.
        if func.__module__ != package.__name__:
            continue

        params = inspect.signature(func).parameters
        pos_args, kw_args = _generate_test_args(func, params, live_user, live_store)

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
