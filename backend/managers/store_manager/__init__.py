from .store_manager import get_store

"""
This module initializes and exposes key components for store management.

It provides:
- `get_store`: A function to retrieve store instances.
- `Store`: The base class representing a store.
- `Listing`: The class representing a product listing within a store.
- `STORE_REGISTRY`: A registry containing available store implementations.

These components are intended to be imported and used by other parts of the
application for managing store-related operations.
"""
from .stores.store import Store
from .stores.listing import Listing
from .stores import STORE_REGISTRY

__all__ = ["get_store", "Store", "Listing", "STORE_REGISTRY"]
