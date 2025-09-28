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
from .db_config import initialize_database, startup_database

# Now that `data.database.schema` is available, we can safely import the repositories.
from .repositories.card_repository import (
    get_users_cards, add_user_card, delete_user_card, update_user_tracked_cards_list,
    update_user_tracked_card_preferences, search_card_names, add_card_names_to_catalog, add_set_data_to_catalog,
    bulk_add_finishes, bulk_add_card_printings, get_all_printings_map, get_all_finishes_map, get_printings_for_card,
    bulk_add_printing_finish_associations
)
from .repositories.user_repository import (
    get_user_by_username, update_username, update_password, add_user, add_user_store,
    remove_user_store, get_user_stores, set_user_stores, get_user_for_display, get_all_users,
    get_users_tracking_card, get_tracking_users_for_cards, get_user_orm_by_id, get_user_orm_by_username
)
from .repositories.store_repository import get_store_metadata, get_all_stores

# Define the public API of the `data.database` package.
__all__ = [
    # Setup
    "initialize_database", "schema", "startup_database"

    # Card Repository
    "get_users_cards", "add_user_card", "delete_user_card",
    "update_user_tracked_cards_list", "update_user_tracked_card_preferences",
    "search_card_names", "add_card_names_to_catalog", "add_set_data_to_catalog", "bulk_add_finishes", "get_printings_for_card",
    "bulk_add_card_printings", "get_all_printings_map", "get_all_finishes_map",
    "bulk_add_printing_finish_associations",
    "get_user_by_username", "update_username", "update_password", "add_user",
    "add_user_store", "remove_user_store", "get_user_stores", "set_user_stores",
    "get_user_for_display", "get_all_users", "get_users_tracking_card",
    "get_tracking_users_for_cards", "get_user_orm_by_id", "get_user_orm_by_username",

    # Store Repository
    "get_store_metadata", "get_all_stores",
]
# This file makes the 'tasks' directory a Python package.
