from typing import Optional

from .stores import STORE_REGISTRY
from .stores import Store


def get_store(store_name: str = "") -> Optional[Store]:
    """
    Retrieves a store instance from the registry.

    If a store_name (slug) is provided, it returns that specific store's
    scraper instance. Otherwise, it returns a list of all store instances.
    """
    if store_name:
        return STORE_REGISTRY.get_registry().get(store_name)
    else:
        return None


def get_stores() -> list[Store]:
    return list(STORE_REGISTRY.get_registry().values())
