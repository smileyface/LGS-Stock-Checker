from .stores import STORE_REGISTRY


def get_store(store_name: str = None):
    """
    Retrieves a store instance from the registry.

    If a store_name (slug) is provided, it returns that specific store's
    scraper instance. Otherwise, it returns a list of all store instances.
    """
    if store_name:
        return STORE_REGISTRY.get_registry().get(store_name)
    return list(STORE_REGISTRY.get_registry().values())
