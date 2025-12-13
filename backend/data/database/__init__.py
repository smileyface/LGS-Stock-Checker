"""
This package provides the primary interface for database operations.

It initializes the database connection and aggregates repository functions
into the `data.database` namespace for convenient access throughout the
application.
e.g., `from data.database import get_user_by_username`

The import order here is critical to avoid circular dependencies.
"""

# To resolve a circular dependency, we must import modules that the
# repositories depend on *before* we import the repositories themselves.
# The repositories depend on `schema`, so we import it first.
from .db_config import initialize_database

from .session_manager import get_session, remove_session, health_check

from .repositories.card_repository import (
    modify_user_tracked_card,
    get_users_cards,
    delete_user_card,
    update_user_tracked_card_preferences,
    search_card_names,
    filter_existing_card_names,
)
from .repositories.user_repository import (
    get_user_by_username,
    update_username,
    update_password,
    add_user,
    add_user_store,
    remove_user_store,
    get_user_stores,
    set_user_stores,
    get_user_for_display,
    get_all_users,
    get_users_tracking_card,
    get_tracking_users_for_cards,
    get_user_orm_by_id,
    get_user_orm_by_username,
    get_user_password_hash,
)
from .repositories.store_repository import (
    get_store_metadata,
    get_all_stores
)
from .repositories.catalogue_repository import (
    add_card_names_to_catalog,
    add_set_data_to_catalog,
    bulk_add_finishes,
    bulk_add_card_printings,
    bulk_add_printing_finish_associations,
    get_all_printings_map,
    get_all_finishes_map,
    get_printings_for_card,
    is_card_in_catalog,
    is_valid_printing_specification,
    get_chunk_printing_ids,
    get_chunk_finish_ids,
)

# Define the public API of the `data.database` package.
__all__ = [
    # Setup
    "initialize_database",
    # Session Manager
    "get_session",
    "remove_session",
    "health_check",
    # Card Repository
    "modify_user_tracked_card",
    "get_users_cards",
    "delete_user_card",
    "update_user_tracked_card_preferences",
    "search_card_names",
    "get_user_by_username",
    "update_username",
    "update_password",
    "add_user",
    "add_user_store",
    "remove_user_store",
    "get_user_stores",
    "set_user_stores",
    "get_user_for_display",
    "get_all_users",
    "get_users_tracking_card",
    "get_tracking_users_for_cards",
    "get_user_orm_by_id",
    "get_user_orm_by_username",
    "is_card_in_catalog",
    "filter_existing_card_names",
    "is_valid_printing_specification",
    "get_user_password_hash",
    # Store Repository
    "get_store_metadata",
    "get_all_stores",
    # Catalogue Repository
    "add_card_names_to_catalog",
    "add_set_data_to_catalog",
    "bulk_add_finishes",
    "get_printings_for_card",
    "bulk_add_card_printings",
    "get_all_printings_map",
    "get_all_finishes_map",
    "bulk_add_printing_finish_associations",
    "is_card_in_catalog",
    "get_chunk_printing_ids",
    "get_chunk_finish_ids",
]
