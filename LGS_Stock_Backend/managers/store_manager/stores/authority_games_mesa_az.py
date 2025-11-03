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
                product_link_tag = product.select_one("a[itemprop='url']")
                product_url = product_link_tag.get("href") if product_link_tag else ""
                full_product_url = urljoin(self.homepage, product_url)

                # Fetch the product page once to get all static details.
                product_page_html = self._get_product_page(product_url)
                static_details = self._parse_product_page_details(product_page_html)

                # Now, parse the variants from the search result to get price/stock.
                variants = self._parse_variants(product)
                for variant_details in variants:
                    listing = {
                        "url": full_product_url,
                        **static_details,  # Add name, set, collector_number, etc.
                        **variant_details,  # Add price, stock, condition
                    }
                    available_products.append(listing)

        return available_products

    def _get_product_listings(self, soup: BeautifulSoup) -> List[Any]:
        return soup.find_all('li', class_='product')

    def _get_set(self, row: BeautifulSoup) -> str:
        set_element = row.find('span', class_='category')
        set_name = set_element.get_text(strip=True) if set_element else 'Unknown'
        logger.debug(f"Set name: {set_name}")
        return set_code(set_name) or set_name

    def _parse_product_page_details(self, html_content: Optional[str]) -> Dict[str, Any]:
        """Parses the product detail page to get canonical card information."""
        if not html_content:
            return {}

        soup = BeautifulSoup(html_content, "html.parser")
        details_section = soup.find("div", class_="product-more-info")
        if not details_section:
            return {}

        details = {}
        
        # Helper to extract text from a detail div
        def get_detail(class_name):
            div = details_section.find("div", class_=class_name)
            if div and div.find("a"):
                return div.find("a").text.strip()
            return None

        details["name"] = get_detail("name")
        details["set"] = set_code(get_detail("set-name"))
        card_number_raw = get_detail("card-number")
        details["collector_number"] = card_number_raw.split("/")[0].strip() if card_number_raw else None
        
        return details

    def _parse_variants(self, product: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parses all in-stock variants from a product listing."""
        variants = []
        for variant_row in product.select("div.variant-row.in-stock"):
            try:
                condition_element = variant_row.select_one(".variant-description")
                price_element = variant_row.select_one(".price")
                qty_element = variant_row.select_one(".variant-qty")

                if not all([condition_element, price_element, qty_element]):
                    continue

                description = condition_element.text.strip()
                condition = description.split(",")[0].strip()
                # The finish is now parsed from the product page, so we only need condition here.

                price_str = price_element.text.strip().replace("$", "").replace(",", "")
                price = float(price_str)

                qty_text = qty_element.text.strip()
                quantity = int(qty_text.split(" ")[0])

                variants.append({
                    "price": price,
                    "stock": quantity,
                    "condition": condition,
                })
            except (ValueError, AttributeError) as e:
                logger.error(f"Failed to parse a variant: {e}")
                continue
        return variants

    def __str__(self):
        return self.name
