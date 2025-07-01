from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup

from managers.set_manager import set_code
from managers.store_manager.stores.store import Store
from utility.logger import logger


class Authority_Games_Mesa_Arizona(Store):
    def __init__(self):
        super().__init__(
            name="Authority Games (Mesa, AZ)",
            slug="authority_games_mesa_az",
            homepage="https://www.authoritygamestore.com/",
            search_url="https://www.authoritygamestore.com/search",
            fetch_strategy="default"
        )

    def _scrape_listings(self, card_name: str) -> List[Dict[str, Any]]:
        """Scrapes the store's website for raw card listings."""
        search_params = {"q": card_name, "c": "1"}
        response = requests.get(self.search_url, params=search_params)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        product_rows = self._get_product_rows(soup)
        available_products = []

        for product_row in product_rows:
            try:
                name = self._get_name(product_row)
                price = self._get_price(product_row)
                stock = self._get_stock(product_row)
                condition = self._get_condition(product_row)
                finish = self._get_finish(product_row)
                set_name = self._get_set(product_row)

                available_products.append({
                    "name": name,
                    "price": price,
                    "stock": stock,
                    "condition": condition,
                    "finish": finish,
                    "set": set_name,
                })
            except Exception as e:
                logger.error(f"Error processing product row for {self.name}: {e}")

        return available_products

    def _get_product_rows(self, soup: BeautifulSoup) -> List[Any]:
        """Find all product rows matching the search query."""
        products_container = soup.find('ul', class_=['products', 'detailed'])
        return products_container.find_all('li', class_='product') if products_container else []

    def _get_name(self, row: BeautifulSoup) -> str:
        name_element = row.find('h4', class_='name')
        return name_element.get_text(strip=True) if name_element else "Unknown"

    def _get_price(self, row: BeautifulSoup) -> str:
        price_element = row.find('div', class_='product-price')
        return price_element.get_text(strip=True) if price_element else "N/A"

    def _get_stock(self, row: BeautifulSoup) -> str:
        stock_element = row.find('span', class_='variant-short-info variant-qty')
        return stock_element.get_text(strip=True) if stock_element else '0 In Stock'

    def _get_condition(self, row: BeautifulSoup) -> str:
        condition_element = row.find('span', class_='variant-short-info variant-description')
        condition_text = condition_element.get_text(strip=True) if condition_element else 'Unknown'
        return condition_text.split(", ")[0]

    def _get_finish(self, row: BeautifulSoup) -> str:
        product_name = self._get_name(row)
        if " - " in product_name:
            return product_name.split(" - ")[1].lower()
        return "normal"

    def _get_set(self, row: BeautifulSoup) -> str:
        set_element = row.find('span', class_='category')
        set_name = set_element.get_text(strip=True) if set_element else 'Unknown'
        return set_code(set_name) or set_name

    def __str__(self):
        return self.name
