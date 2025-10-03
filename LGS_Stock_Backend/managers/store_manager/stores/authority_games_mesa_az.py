from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup

from managers.set_manager import set_code
from managers.store_manager.stores.store import Store
from utility import logger


class Authority_Games_Mesa_Arizona(Store):
    def __init__(self):
        super().__init__(
            name="Authority Games (Mesa, AZ)",
            slug="authority_games_mesa_az",
            homepage="https://authoritygames.crystalcommerce.com/",
            search_url="https://authoritygames.crystalcommerce.com/products/search?",
            fetch_strategy="default"
        )

    def _scrape_listings(self, card_name: str) -> List[Dict[str, Any]]:
        """Scrapes the store's website for raw card listings."""
        search_params = {"q": card_name, "c": "1"}
        response = requests.get(self.search_url, params=search_params)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        product_listings = self._get_product_listings(soup)
        available_products = []

        for listing in product_listings:
            name = self._get_name(listing)
            set_name = self._get_set(listing)
            
            variant_rows = listing.find_all('div', class_='variant-row')
            for variant in variant_rows:
                try:
                    price = self._get_price(variant)
                    stock = self._get_stock(variant)
                    condition = self._get_condition(variant)
                    finish = self._get_finish(variant)


                    available_products.append({
                        "name": name,
                        "price": price,
                        "stock": stock,
                        "condition": condition,
                        "finish": finish,
                        "set": set_name,
                    })
                except Exception as e:
                    logger.error(f"Error processing variant row for {self.name}: {e}")


        return available_products

    def _get_product_listings(self, soup: BeautifulSoup) -> List[Any]:
        """Find all product listings from the search results fragment."""
        # The search_results endpoint returns a list of <li>s directly.
        return soup.find_all('li', class_='product')

    def _get_name(self, listing: BeautifulSoup) -> str:
        name_element = listing.find('h4', class_='name')
        return name_element.get_text(strip=True) if name_element else "Unknown"

    def _get_price(self, row: BeautifulSoup) -> str:
        price_element = row.find('div', class_='product-price')
        return price_element.get_text(strip=True) if price_element else "N/A"

    def _get_stock(self, row: BeautifulSoup) -> int:
        """Extracts the stock quantity as an integer."""
        stock_element = row.find('span', class_='variant-short-info variant-qty')
        if not stock_element:
            return 0
        
        stock_text = stock_element.get_text(strip=True)  # e.g., "5 In Stock"
        try:
            # Extract the number from the string.
            return int(stock_text.split()[0])
        except (ValueError, IndexError):
            logger.warning(f"Could not parse stock quantity from '{stock_text}' for {self.name}. Assuming 0.")
            return 0

    def _get_condition(self, row: BeautifulSoup) -> str:
        condition_element = row.find('span', class_='variant-short-info variant-description')
        condition_text = condition_element.get_text(strip=True) if condition_element else 'Unknown'
        return condition_text.split(", ")[0]

    def _get_finish(self, row: BeautifulSoup) -> str:
        """Extracts the finish from the variant description text."""
        condition_element = row.find('span', class_='variant-short-info variant-description')
        condition_text = condition_element.get_text(strip=True).lower() if condition_element else ''
        if 'foil' in condition_text:
            return 'foil'
        return "non-foil"

    def _get_set(self, row: BeautifulSoup) -> str:
        set_element = row.find('span', class_='category')
        set_name = set_element.get_text(strip=True) if set_element else 'Unknown'
        return set_code(set_name) or set_name

    def __str__(self):
        return self.name
