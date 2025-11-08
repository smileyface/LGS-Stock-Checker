"""
This module dynamically loads and registers store scraper instances.

On startup, it queries the database for all available stores, determines the
correct scraper class to use based on the store's `fetch_strategy`, and
instantiates an object for each one. The resulting instances are stored in
the `STORE_REGISTRY`, making them available to the rest of the application.
"""
from utility import logger
from .storefronts.crystal_commerce_store import CrystalCommerceStore
from .storefronts.default import DefaultStore

class LazyStoreRegistry:
    """
    A lazy-loading registry for store scrapers.
    
    This class avoids querying the database at import time. It populates the
    store registry only when it's first accessed, ensuring that the database
    has been initialized by the application factory before any queries are made.
    """
    def __init__(self):
        self._registry = None
        self._strategy_map = {
            "crystal_commerce": CrystalCommerceStore,
            "default": DefaultStore,
        }
    
    @property
    def keys(self):
        """Returns the keys (slugs) of the store registry, triggering a lazy load if necessary."""
        return list(self.get_registry().keys())
    
    def _load_stores(self):
        logger.info("🔧 Lazily loading store registry from database...")
        # This import is intentionally placed here to avoid circular dependencies
        # and ensure the data layer is ready.
        from data import database
        
        self._registry = {}
        all_stores_from_db = database.get_all_stores()
        for store_model in all_stores_from_db:
            strategy = store_model.fetch_strategy
            if strategy in self._strategy_map:
                StoreClass = self._strategy_map[strategy]
                instance = StoreClass(
                    name=store_model.name,
                    slug=store_model.slug,
                    homepage=store_model.homepage,
                    search_url=store_model.search_url,
                )
                self._registry[instance.slug] = instance
        logger.info(f"✅ Store registry loaded with {len(self._registry)} stores.")
    
    def get_registry(self):
        if self._registry is None:
            self._load_stores()
        return self._registry

STORE_REGISTRY = LazyStoreRegistry()
