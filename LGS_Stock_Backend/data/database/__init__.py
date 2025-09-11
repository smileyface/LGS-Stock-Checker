"""
This package provides the primary interface for database operations.

It initializes the database connection and aggregates repository functions
into the `data.database` namespace for convenient access throughout the application.
e.g., `from data.database import get_user_by_username`

The import order here is critical to avoid circular dependencies.
"""

# To resolve a circular dependency, we must import modules that the repositories
# depend on *before* we import the repositories themselves.
# The repositories depend on `schema`, so we import it first.
from . import schema
from .db_config import init_db

# Now that `data.database.schema` is available, we can safely import the repositories.
from .repositories.card_repository import (
    get_users_cards, add_user_card, delete_user_card, update_user_tracked_cards_list,
    update_user_tracked_card_preferences
)
from .repositories.user_repository import (
    get_user_by_username, update_username, update_password, add_user, add_user_store,
    remove_user_store, get_user_stores, get_user_for_display, get_all_users,
    get_users_tracking_card, get_tracking_users_for_cards
)
from .repositories.store_repository import get_store_metadata, get_all_stores

# Define the public API of the `data.database` package.
__all__ = [
    # Setup
    "init_db", "schema",

    # Card Repository
    "get_users_cards", "add_user_card", "delete_user_card",
    "update_user_tracked_cards_list", "update_user_tracked_card_preferences",

    # User Repository
    "get_user_by_username", "update_username", "update_password", "add_user",
    "add_user_store", "remove_user_store", "get_user_stores",
    "get_user_for_display", "get_all_users", "get_users_tracking_card",
    "get_tracking_users_for_cards",

    # Store Repository
    "get_store_metadata", "get_all_stores",
]

# Initialize the database by creating tables when this package is first imported.
# This is idempotent and safe to run on every application startup.
init_db()
