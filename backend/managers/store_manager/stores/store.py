from abc import ABC, abstractmethod
from typing import Any, Dict, List

import requests

from managers.store_manager.filtering import filter_listings
from utility import logger


class Store(ABC):
    """Abstract base class for all store implementations."""

    def __init__(self, name: str, slug: str, homepage: str, search_url: str):
        self.name = name
        self.slug = slug
        self.homepage = homepage
        self.search_url = search_url

    @abstractmethod
    def _scrape_listings(self, card_name: str) -> List[Dict[str, Any]]:
        """
        Scrapes the store's website for raw card listings.
        This method must be implemented by each subclass.
        """
        pass  # pragma: no cover

    def fetch_card_availability(self, card_name: str, specifications: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Fetches and filters card availability from the store."""
        logger.info(f"🔄 Starting availability check for '{card_name}' at {self.name}")
        try:
            raw_listings = self._scrape_listings(card_name)
            logger.info(f"✅ Found {len(raw_listings)} raw listings for '{card_name}' at {self.name}")
            return filter_listings(card_name, raw_listings, specifications)
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error connecting to {self.name}: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ An error occurred while checking availability for '{card_name}' at {self.name}: {e}")
            return []
