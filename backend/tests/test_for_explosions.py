import importlib
import inspect
import pkgutil
import warnings
import typing
import logging
from unittest.mock import MagicMock

from datetime import datetime
import pytest
from tests.fixtures.db_fixtures import seed_user, seed_stores
from werkzeug.exceptions import HTTPException
from flask_socketio import SocketIO
from data.database.models.orm_models import Store, User
import managers
import utility
import data
import routes
import tasks


def import_all_modules_from_packages(*packages):
    """Dynamically imports all submodules from multiple packages
    and prints successful imports."""
    modules = []
    for package in packages:
        for _, module_name, _ in pkgutil.walk_packages(
            package.__path__, package.__name__ + "."
        ):
            try:
                module = importlib.import_module(module_name)
                modules.append(module)
                # print(f"✅ Successfully imported {module_name}")
            except ImportError as e:
                warnings.warn(f"⚠️ Failed to import {module_name}: {e}")
    return modules


PACKAGES_TO_TEST = import_all_modules_from_packages(
    managers, data, utility, routes, tasks
)


def _get_arg_from_known_names(param_name,
                              func,
                              live_user,
                              live_store,
                              data_payloads):
    """Generate arguments based on specific, known parameter names."""
    if func.__name__ == "add_user" and "username" in param_name:
        # Generate a unique username for each call to prevent IntegrityError
        return f"new_smoke_test_user_{datetime.now().timestamp()}"
    if param_name == "app":
        mock_app = MagicMock()
        mock_app.config = {}
        return mock_app
    if param_name == "data" and func.__name__ in data_payloads:
        return data_payloads[func.__name__]
    if "user" in param_name and ("name" in param_name or
                                 "username" in param_name):
        return live_user.username
    if "user" in param_name and "id" in param_name:
        return live_user.id
    if "store" in param_name and "id" in param_name:
        return live_store.id
    if param_name == "store_slugs":
        return [live_store.slug]
    if "slug" in param_name:
        return live_store.slug
    if "password" in param_name and "hash" not in param_name:
        return "a_valid_password"
    if "password_hash" in param_name:
        return "a_valid_test_hash"
    return None  # Sentinel value indicating no match


def _get_arg_from_type_hint(param, live_user, live_store):
    """Generate arguments based on type hints."""
    annotation = param.annotation
    origin = typing.get_origin(annotation)

    # Handle Optional[T] by trying to resolve T
    if origin is typing.Union and type(None) in typing.get_args(annotation):
        # Find the first non-None type in Optional[T, U, ...]
        non_none_type = next(
            (t for t in typing.get_args(annotation) if t is not type(None)),
            None,
        )
        if non_none_type:
            annotation = (
                # Try to generate a value for the underlying type
                non_none_type
            )

    # Handle specific ORM model types
    if annotation is User:
        return live_user
    if annotation is Store:
        return live_store
    if annotation is logging.Logger:
        return MagicMock()

    # Handle common non-trivial types
    if annotation is callable:
        return lambda: "dummy function"
    if annotation is SocketIO:
        return MagicMock()

    # Fallback to generic types
    if hasattr(annotation, "__total__"):  # Heuristic for TypedDict
        return {}
    if annotation is dict or origin is dict:
        return {}
    if annotation is list or origin is list:
        return []
    if annotation is str:
        return "test_string"
    if annotation is int:
        return 1
    if annotation is float:
        return 1.0
    if annotation is datetime:
        return datetime.now()
    if annotation is bool:
        return False
    return None  # Sentinel value indicating no match


def _generate_test_args(func, params, live_user, live_store):
    """
    Generates positional and keyword arguments for a function based on
    its signature, using seeded data and safe defaults.
    """
    pos_args = []
    kw_args = {}

    # A mapping for functions that expect a specific 'data' payload.
    data_payloads = {
        "handle_get_card_printings": {"card_name": "test_card"},
        "handle_add_user_tracked_card": {
            "card": "test_card",
            "amount": 1,
            "card_specs": {},
        },
        "handle_delete_user_tracked_card": {"card": "test_card"},
        "handle_update_user_tracked_cards": {
            "card": "test_card",
            "update_data": {"amount": 2},
        },
        "handle_update_user_stores": {"stores": ["test_store"]},
    }

    for param_name, param in params.items():
        is_kw_only = param.kind == inspect.Parameter.KEYWORD_ONLY

        # Skip variable-length positional and keyword arguments (*args,
        # **kwargs)
        if param.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue

        # Skip dependency-injected database sessions provided by the
        # @db_query decorator.
        if param_name == "session":
            continue  # The @db_query decorator injects the session; skip.

        # --- Argument Generation Strategy ---
        # 1. Try to generate an argument based on known parameter names.
        arg_value = _get_arg_from_known_names(
            param_name, func, live_user, live_store, data_payloads
        )

        # 2. If not found, try to generate based on type hints.
        if arg_value is None:
            arg_value = _get_arg_from_type_hint(param, live_user, live_store)

        # 3. If still not found, use the parameter's default value,
        # if it exists.
        if arg_value is None and param.default is not inspect.Parameter.empty:
            arg_value = param.default

        # 4. As a final fallback, the value remains None.

        if is_kw_only:
            kw_args[param_name] = arg_value
        else:
            pos_args.append(arg_value)

    return pos_args, kw_args


@pytest.mark.smoke
@pytest.mark.parametrize(
    "package", PACKAGES_TO_TEST, ids=[p.__name__ for p in PACKAGES_TO_TEST]
)
def test_all_functions_no_crashes(
    package, db_session, mocker, seeded_user, seeded_store
):
    """
    Smoke test to ensure that functions can be called with basic, safe inputs
    without raising exceptions. This test uses seeded data for more
    realistic scenarios.
    """
    # Mock the underlying get_json method to prevent crashes in route handlers
    # that access request.json without the correct Content-Type header.
    mocker.patch("werkzeug.wrappers.request.Request.get_json", return_value={})

    # Mock get_redis_connection where it is defined to cover most cases.
    mocker.patch(
        "managers.redis_manager.redis_manager.get_redis_connection",
        return_value=MagicMock(),
    )
    # Also mock it where it's imported and used in cache_manager to ensure
    # it's caught.
    mocker.patch(
        "data.cache.cache_manager.redis_manager.get_redis_connection",
        return_value=MagicMock(),
    )

    # Explicitly mock the scheduler for the smoke test. This prevents functions
    # like `_schedule_if_not_exists` from making real Redis calls, which is the
    # most common source of network-related failures in this test.
    mocker.patch("managers.redis_manager.scheduler", return_value=MagicMock())

    # For tasks, we don't want to hit the real Scryfall API.
    # Mock the fetch functions to return controlled, small datasets.
    if package.__name__.startswith("tasks"):
        mocker.patch(
            "tasks.catalog_tasks.fetch_scryfall_card_names",
            return_value=["Card A", "Card B"],
        )
        mocker.patch("tasks.catalog_tasks.fetch_all_sets", return_value=[])

        mock_store_instance = MagicMock()
        mock_store_instance.fetch_card_availability.return_value = []
        mocker.patch(
            "managers.store_manager.get_store",
            return_value=mock_store_instance
        )

    for name, func in inspect.getmembers(package, inspect.isfunction):
        # Ensure we only test functions defined in the current package,
        # not imported ones.
        if func.__module__ != package.__name__:
            continue

            # Skip app factory functions as they require a specific setup
            # context provided by fixtures, not the generic argument
            # generation.
        if name in (
            "initalize_flask_app",
            "create_app",
            "initialize_redis",
            "configure_socket_io",
        ):
            continue

        # --- State Reset ---
        # For each function, clear all tables and re-seed the database.
        # This provides a clean, isolated environment for every function call,
        # preventing data from one call from interfering with the next.
        for table in reversed(User.metadata.sorted_tables):
            db_session.execute(table.delete())
        db_session.commit()
        live_user = seed_user(db_session)
        live_store = seed_stores(db_session)[0]  # Get the first store

        params = inspect.signature(func).parameters
        pos_args, kw_args = _generate_test_args(func,
                                                params,
                                                live_user,
                                                live_store)

        try:
            func(*pos_args, **kw_args)
        except HTTPException:
            # HTTP exceptions (like 401 Unauthorized or 404 Not Found) are
            # expected outcomes
            # for route handlers when called without a proper request context.
            # We consider this a "pass" for a smoke test, as the function
            # didn't crash
            # due to a programming error.
            pass
        except Exception as e:
            pytest.fail(
                f"Function {package.__name__}.{name}{inspect.signature(func)} "
                f"raised an exception with args {pos_args} and kwargs"
                f" {kw_args}: {e}"
            )
