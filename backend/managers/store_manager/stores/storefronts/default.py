"""
This module defines the default Store class, which serves as a fallback
for stores that do not have a specific scraping strategy defined.

It inherits from the abstract base class `Store` and provides a basic
implementation for `_scrape_listings` that always returns an empty list,
effectively indicating that no listings can be found for such stores.
"""
from typing import Any, Dict, List

from managers.store_manager.stores.store import Store
from utility import logger


class DefaultStore(Store):
    """
    A default store implementation for cases where no specific scraping
    strategy is defined.

    This class provides a placeholder `_scrape_listings` method that
    always returns an empty list, as it does not implement any actual
    scraping logic. It serves as a safe fallback to prevent errors
    when an unknown `fetch_strategy` is encountered.
    """

    def __init__(self, name: str, slug: str, homepage: str, search_url: str):
        # Default stores don't have a meaningful search_url for scraping,
        # but the base class requires it. We can pass an empty string.
        super().__init__(name, slug, homepage, search_url=search_url)
        logger.warning(
            f"⚠️ Initialized DefaultStore for '{name}' (slug: {slug}). "
            "This store does not have a specific scraping strategy and will "
            "not return any card listings."
        )

    def _scrape_listings(self, card_name: str) -> List[Dict[str, Any]]:
        """
        Default implementation for scraping listings.

        Since this is a fallback class, it does not perform any actual
        scraping and always returns an empty list.
        """
        logger.info(
            f"ℹ️ DefaultStore for '{self.name}' was called to scrape '{card_name}'. "
            "Returning an empty list as no scraping strategy is implemented."
        )
        return []
