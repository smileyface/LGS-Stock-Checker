from typing import Any, Dict, List, Optional
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from managers.set_manager import set_code
from managers.store_manager.stores.store import Store
from utility import logger

class Authority_Games_Mesa_Arizona(Store):
    def __init__(self):
        super().__init__(
            name="Authority Games (Mesa, AZ)",
            slug="authority_games_mesa_az",
            homepage="https://authoritygames.crystalcommerce.com/",
            search_url="https://authoritygames.crystalcommerce.com/products/search",
            fetch_strategy="default"
        )

    def _get_product_page(self, product_url: str) -> Optional[str]:
        """Fetches the individual product page to find the collector number."""
        full_url = urljoin(self.homepage, product_url)
        try:
            response = requests.get(full_url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch product page for {self.name}. URL: {full_url}, Error: {e}")
            return None

    def _parse_collector_number(self, html_content: Optional[str]) -> Optional[str]:
        """Parses the product page HTML to extract the collector number."""
        if not html_content:
            return None

        soup = BeautifulSoup(html_content, "html.parser")
        card_number_div = soup.find("div", class_="card-number")
        if card_number_div:
            collector_number_tag = card_number_div.find("a")
            if collector_number_tag and collector_number_tag.text.strip():
                collector_number = collector_number_tag.text.strip().split("/")[0]
                logger.debug(f"Found collector number: {collector_number}")
                return collector_number
        logger.debug("Collector number not found on product page.")
        return None

    def _scrape_listings(self, card_name: str) -> List[Dict[str, Any]]:
        """Scrapes the store's website for raw card listings."""
        try:
            search_params = {"q": card_name, "c": 1}
            response = requests.get(self.search_url, params=search_params, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
        except requests.RequestException as e:
            logger.error(f"Failed to fetch search results for {self.name}. Card: {card_name}, Error: {e}")
            return []
        product_listings = self._get_product_listings(soup)
        available_products = []

        if product_listings:
            for product in product_listings:
                name = self._get_name(product)
                set_name = self._get_set(product)
                product_link_tag = product.select_one("a[itemprop='url']")
                product_url = product_link_tag.get("href") if product_link_tag else ""
                full_product_url = urljoin(self.homepage, product_url)
    
                # --- New logic to fetch collector number ---
                collector_number = None
                if product_url:
                    product_page_html = self._get_product_page(product_url)
                    collector_number = self._parse_collector_number(product_page_html)
    
                variants = product.select("div.variant-row.in-stock")
                for variant in variants:
                    condition_element = variant.select_one(".variant-description")
                    price_element = variant.select_one(".price")
                    qty_element = variant.select_one(".variant-qty")
    
                    if not all([condition_element, price_element, qty_element]):
                        continue
    
                    condition = condition_element.text.strip().split(",")[0]
                    price_str = price_element.text.strip().replace("$", "")
                    qty_text = qty_element.text.strip()
                    quantity = int(qty_text.split(" ")[0])
                    finish = "foil" if "foil" in condition_element.text.strip().lower() else "non-foil"
    
                    available_products.append({
                        "name": name,
                        "price": float(price_str),
                        "stock": quantity,
                        "condition": condition,
                        "finish": finish,
                        "set": set_name,
                        "collector_number": collector_number,
                        "url": full_product_url,
                    })

        return available_products

    def _get_product_listings(self, soup: BeautifulSoup) -> List[Any]:
        return soup.find_all('li', class_='product')

    def _get_name(self, listing: BeautifulSoup) -> str:
        name_element = listing.find('h4', class_='name')
        name_element = name_element.get_text(strip=True) if name_element else "Unknown"
        logger.debug(f"Name element: {name_element}")
        return name_element

    def _get_set(self, row: BeautifulSoup) -> str:
        set_element = row.find('span', class_='category')
        set_name = set_element.get_text(strip=True) if set_element else 'Unknown'
        logger.debug(f"Set name: {set_name}")
        return set_code(set_name) or set_name

    def __str__(self):
        return self.name
