"""
Provides a standardized base class for scraping stores that use the
Crystal Commerce e-commerce platform.

This class encapsulates the common logic for fetching and parsing product data,
allowing new Crystal Commerce stores to be added with minimal code.
"""
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from LGS_Stock_Backend.managers.set_manager import set_code
from LGS_Stock_Backend.managers.store_manager.stores.store import Store
from LGS_Stock_Backend.utility import logger


class CrystalCommerceStore(Store):
    """
    A base class for scraping stores built on the Crystal Commerce platform.

    It implements the common scraping logic for searching products, parsing
    variants, and extracting details from product pages. Subclasses only need
    to provide their specific metadata (name, slug, URLs).
    """

    def _get_product_page(self, product_url: str) -> Optional[str]:
        """Fetches the individual product page to find the collector number."""
        full_url = urljoin(self.homepage, product_url)
        logger.debug(f"Fetching product page for {self.name}. URL: {full_url}")
        try:
            response = requests.get(full_url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(
                f"Failed to fetch product page for {self.name}. URL: {full_url}, Error: {e}"
            )
            return None

    def _scrape_listings(self, card_name: str) -> List[Dict[str, Any]]:
        """Scrapes the store's website for raw card listings."""
        try:
            search_params = {"q": card_name, "c": 1}
            response = requests.get(self.search_url, params=search_params, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as e:
            logger.error(
                f"Failed to fetch search results for {self.name}. Card: {card_name}, Error: {e}"
            )
            return []

        product_listings = self._get_product_listings(soup)
        available_products = []
        seen_listings = set()  # To track and prevent duplicate listings

        if product_listings:
            for product in product_listings:
                name_element = product.select_one("h4.name")
                scraped_card_name = (
                    name_element.get("title", "").strip() if name_element else ""
                )
                scraped_card_name = scraped_card_name.split(" - ")[0]

                if not scraped_card_name or scraped_card_name.lower() != card_name.lower():
                    logger.debug(
                        f"Found non-matching result '{scraped_card_name}'. Assuming no more exact matches and stopping search."
                    )
                    break

                product_link_tag = product.select_one("a[itemprop='url']")
                product_url = product_link_tag.get("href") if product_link_tag else ""
                full_product_url = urljoin(self.homepage, product_url)

                product_page_html = self._get_product_page(product_url)
                static_details = self._parse_product_page_details(product_page_html)

                variants = self._parse_variants(product)
                for variant_details in variants:
                    listing = {
                        "url": full_product_url,
                        **static_details,
                        **variant_details,
                    }

                    listing_id = (
                        listing.get("name"),
                        listing.get("set_code"),
                        listing.get("collector_number"),
                        listing.get("finish"),
                        listing.get("price"),
                        listing.get("condition"),
                    )
                    if listing_id not in seen_listings:
                        available_products.append(listing)
                        seen_listings.add(listing_id)

        return available_products

    def _get_product_listings(self, soup: BeautifulSoup) -> List[Any]:
        """Finds all product listing elements on a search results page."""
        return soup.find_all("li", class_="product")

    def _parse_product_page_details(
        self, html_content: Optional[str]
    ) -> Dict[str, Any]:
        """Parses the product detail page to get canonical card information."""
        if not html_content:
            return {}

        soup = BeautifulSoup(html_content, "html.parser")
        details_section = soup.find("div", class_="product-more-info")
        if not details_section:
            return {}

        details = {}

        def get_detail(class_name):
            div = details_section.find("div", class_=class_name)
            if div and div.find("a"):
                return div.find("a").text.strip()
            return None

        details["name"] = get_detail("name")
        details["set_code"] = set_code(get_detail("set-name"))
        card_number_raw = get_detail("card-number")
        details["collector_number"] = (
            card_number_raw.split("/")[0].strip() if card_number_raw else None
        )
        return details

    def _parse_variants(self, product: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parses all in-stock variants from a product listing element."""
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
                finish = "foil" if "foil" in description.lower() else "non-foil"
                price_str = price_element.text.strip().replace("$", "").replace(",", "")
                price = float(price_str)
                qty_text = qty_element.text.strip()
                quantity = int(qty_text.split(" ")[0])

                variants.append(
                    {"finish": finish, "price": price, "stock": quantity, "condition": condition}
                )
            except (ValueError, AttributeError) as e:
                logger.error(f"Failed to parse a variant: {e}")
                continue
        return variants
