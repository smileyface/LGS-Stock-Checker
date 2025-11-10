"""
Unit tests for the CrystalCommerceStore base scraper.
"""
import unittest
from unittest.mock import patch, MagicMock
import requests
from bs4 import BeautifulSoup

from managers.store_manager.stores.storefronts.crystal_commerce_store import CrystalCommerceStore, _make_request_with_retries
from managers.store_manager.stores.listing import Listing

# --- Sample HTML Payloads ---
# This is a simplified version of the search results page HTML.
SEARCH_RESULTS_HTML = """
<ul class="products">
  <li class="product">
    <a itemprop="url" href="/products/1234-test-card"></a>
    <h4 class="name" title="Test Card">Test Card</h4>
    <span class="category">Magic The Gathering: Test Set</span>
    <div class="variants">
      <div class="variant-row in-stock">
        <div class="variant-description">Near Mint</div>
        <div class="price">$10.00</div>
        <div class="variant-qty">2 In Stock</div>
      </div>
      <div class="variant-row in-stock">
        <div class="variant-description">Near Mint, Foil</div>
        <div class="price">$25.00</div>
        <div class="variant-qty">1 In Stock</div>
      </div>
    </div>
  </li>
</ul>
"""

# This is a simplified version of the individual product page HTML.
PRODUCT_PAGE_HTML = """
<div class="product-more-info">
    <div class="name"><a>Test Card</a></div>
    <div class="set-name"><a>Magic The Gathering: Test Set</a></div>
    <div class="card-number"><a>123/456</a></div>
    <div class="finish">
        <!-- The presence or absence of this div determines the finish -->
    </div>
</div>
"""

# This HTML contains two identical variants to test the deduplication logic.
SEARCH_RESULTS_HTML_WITH_DUPLICATES = """
<ul class="products">
  <li class="product">
    <a itemprop="url" href="/products/1234-test-card"></a>
    <h4 class="name" title="Test Card">Test Card</h4>
    <span class="category">Magic The Gathering: Test Set</span>
    <div class="variants">
      <div class="variant-row in-stock"><div class="variant-description">Near Mint</div><div class="price">$10.00</div><div class="variant-qty">2 In Stock</div></div>
      <div class="variant-row in-stock"><div class="variant-description">Near Mint</div><div class="price">$10.00</div><div class="variant-qty">2 In Stock</div></div>
      <div class="variant-row in-stock"><div class="variant-description">Lightly Played</div><div class="price">$8.00</div><div class="variant-qty">1 In Stock</div></div>
    </div>
  </li>
</ul>
"""

# This HTML tests the early-exit logic. It has a valid card, then a non-matching card,
# then another valid card. The scraper should stop after the non-matching card.
SEARCH_RESULTS_WITH_NON_MATCHING_HTML = """
<ul class="products">
  <li class="product">
    <a itemprop="url" href="/products/1234-test-card-1"></a>
    <h4 class="name" title="Test Card">Test Card</h4>
    <span class="category">Magic The Gathering: Test Set</span>
    <div class="variants">
      <div class="variant-row in-stock"><div class="variant-description">Near Mint</div><div class="price">$10.00</div><div class="variant-qty">2 In Stock</div></div>
    </div>
  </li>
  <li class="product">
    <a itemprop="url" href="/products/5678-wrong-card"></a>
    <h4 class="name" title="Wrong Card">Wrong Card</h4>
  </li>
  <li class="product">
    <a itemprop="url" href="/products/9012-test-card-2"></a>
    <h4 class="name" title="Test Card">Test Card</h4>
  </li>
</ul>
"""
# This HTML is missing the 'variants' div entirely.
SEARCH_RESULTS_NO_VARIANTS = """
<ul class="products">
  <li class="product">
    <a itemprop="url" href="/products/1234-test-card"></a>
    <h4 class="name" title="Test Card">Test Card</h4>
    <span class="category">Magic The Gathering: Test Set</span>
  </li>
</ul>
"""

# This HTML tests that the scraper prioritizes the `data-price` attribute on the form
# over the text inside the `span.price` element.
SEARCH_RESULTS_WITH_DATA_PRICE = """
<ul class="products">
  <li class="product">
    <div class="variants">
      <div class="variant-row in-stock">
        <form class="add-to-cart-form" data-price="$12.34">
            <div class="variant-description">Near Mint</div>
            <span class="price">$99.99</span> <!-- This is a decoy price -->
            <div class="variant-qty">5 In Stock</div>
        </form>
      </div>
    </div>
  </li>
</ul>
"""

class TestCrystalCommerceStore(unittest.TestCase): # Renamed from TestAuthorityGamesMesaArizona
    """Tests for the CrystalCommerceStore base scraper.""" # Docstring updated
    def setUp(self):
        """Set up the test case."""
        self.scraper = CrystalCommerceStore( # This was already correct
            name="Test Crystal Commerce Store",
            slug="test-cc-store",
            homepage="https://test-store.crystalcommerce.com/",
            search_url="https://test-store.crystalcommerce.com/products/search"
        )
        
    def mock_requests_get(self, url, params=None, timeout=None):
        """
        A custom mock function for requests.get.
        It returns different HTML based on the URL being requested.
        """
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None

        # If it's a search URL, return the search results HTML.
        if "products/search" in url:
            mock_response.text = SEARCH_RESULTS_HTML
            print(f"Mocking search request for URL: {url}")
        # If it's a product detail URL, return the product page HTML.
        elif "/products/1234-test-card" in url:
            mock_response.text = PRODUCT_PAGE_HTML
            print(f"Mocking product page request for URL: {url}")
        else:
            # Return an empty response for any unexpected URLs.
            mock_response.text = ""
            mock_response.status_code = 404
            print(f"Warning: Unhandled mock request for URL: {url}")

        return mock_response

    @patch('managers.store_manager.stores.storefronts.crystal_commerce_store._make_request_with_retries')
    @patch.object(Listing, 'set_code', autospec=True)
    def test_scrape_listings_success(self, mock_set_code, mock_make_request):
        """
        Test the full scraping process for a card, mocking both network calls.
        """

        # --- Arrange ---
        def set_code_side_effect(listing_instance, set_name):
            listing_instance.set_code = set_name
        # Configure the mock to use our side_effect function
        mock_make_request.side_effect = self.mock_requests_get
        # Configure mock_set_code to return the expected 'tst' for any input
        mock_set_code.side_effect = set_code_side_effect
        
        # --- Execute ---
        card_name = "Test Card"
        listings = self.scraper._scrape_listings(card_name)

        # --- Assert ---
        self.assertEqual(len(listings), 2, "Should find two listings (one regular, one foil)")

        # Verify the first listing (Non-Foil)
        listing1 = listings[0]
        self.assertEqual(listing1.name, "Test Card")
        self.assertEqual(listing1.price, 10.00)
        self.assertEqual(listing1.stock, 2)
        self.assertEqual(listing1.condition, "Near Mint")
        self.assertEqual(listing1.finish, "non-foil")
        self.assertEqual(listing1.set_code, "tst")
        self.assertEqual(listing1.collector_number, "123")
        self.assertIn("/products/1234-test-card", listing1.url)

        # Verify the second listing (Foil)
        listing2 = listings[1]
        self.assertEqual(listing2.name, "Test Card")
        self.assertEqual(listing2.price, 25.00)
        self.assertEqual(listing2.stock, 1)
        self.assertEqual(listing2.condition, "Near Mint")
        self.assertEqual(listing2.finish, "foil")
        self.assertEqual(listing2.collector_number, "123") # Both variants share the collector number

        # Verify that requests.get was called correctly
        self.assertEqual(mock_make_request.call_count, 2, "Should make one call for search and one for the product page")
        
        # Check the first call (search)
        search_call_args = mock_make_request.call_args_list[0]
        self.assertEqual(search_call_args.kwargs['params'], {'q': 'Test Card', 'c': 1})
        
        # Check the second call (product page)
        product_page_call_args = mock_make_request.call_args_list[1]
        self.assertIn('/products/1234-test-card', product_page_call_args.args[0])
        
        # Verify that set_code was called with the correct set name from the HTML
        mock_set_code.assert_called_with("Magic The Gathering: Test Set")

    @patch('managers.store_manager.stores.storefronts.crystal_commerce_store._make_request_with_retries')
    @patch.object(Listing, 'set_code')
    def test_scrape_listings_deduplicates_results(self, mock_set_code, mock_make_request):
        """
        Test that the scraper correctly deduplicates listings when the source HTML
        contains identical variants.
        """
        # --- Arrange ---
        # Mock the response for the search page to return the HTML with duplicates.
        mock_search_response = MagicMock()
        mock_search_response.raise_for_status.return_value = None
        mock_search_response.text = SEARCH_RESULTS_HTML_WITH_DUPLICATES

        # Mock the response for the product detail page.
        mock_product_response = MagicMock()
        mock_product_response.raise_for_status.return_value = None
        mock_product_response.text = PRODUCT_PAGE_HTML

        # Set the side_effect to return the correct mock response based on the URL.
        mock_make_request.side_effect = [mock_search_response, mock_product_response]
        mock_set_code.return_value = "tst"

        # --- Execute ---
        card_name = "Test Card"
        listings = self.scraper._scrape_listings(card_name)

        # --- Assert ---
        # The source HTML has 3 variants, but 2 are identical.
        # The scraper should return only 2 unique listings.
        self.assertEqual(len(listings), 2, "Should find 2 unique listings after deduplication")

    @patch('managers.store_manager.stores.storefronts.crystal_commerce_store._make_request_with_retries')
    @patch.object(Listing, 'set_code')
    def test_scrape_listings_stops_on_non_matching_card(self, mock_set_code, mock_make_request):
        """
        Test that the scraper stops processing once it encounters a card that
        does not match the search term.
        """
        # --- Arrange ---
        mock_search_response = MagicMock()
        mock_search_response.raise_for_status.return_value = None
        mock_search_response.text = SEARCH_RESULTS_WITH_NON_MATCHING_HTML

        mock_product_response = MagicMock()
        mock_product_response.raise_for_status.return_value = None
        mock_product_response.text = PRODUCT_PAGE_HTML

        # The scraper should only request the first product page, then stop.
        mock_make_request.side_effect = [mock_search_response, mock_product_response]
        mock_set_code.return_value = "tst"

        # --- Execute ---
        card_name = "Test Card"
        listings = self.scraper._scrape_listings(card_name)

        # --- Assert ---
        # It should only find the one listing from the first product.
        self.assertEqual(len(listings), 1, "Should only process listings before the non-matching card")

        # It should have made one call for the search page and one for the first product page.
        # It should NOT have made a call for the second "Test Card" after the "Wrong Card".
        self.assertEqual(mock_make_request.call_count, 2, "Should stop making requests after a non-match")

    @patch('managers.store_manager.stores.storefronts.crystal_commerce_store._make_request_with_retries')
    def test_scrape_listings_search_network_failure(self, mock_make_request):
        """
        Test that _scrape_listings handles a network error during the initial search
        and returns an empty list without crashing.
        """
        # --- Arrange ---
        # Configure the mock to raise a RequestException, simulating a network failure.
        mock_make_request.return_value = None
        card_name = "Test Card"

        # --- Execute ---
        listings = self.scraper._scrape_listings(card_name)

        # --- Assert ---
        self.assertEqual(listings, [])
        mock_make_request.assert_called_once()

    @patch('managers.store_manager.stores.storefronts.crystal_commerce_store._make_request_with_retries')
    def test_scrape_listings_product_page_network_failure(self, mock_make_request):
        """
        Test that _scrape_listings handles a network failure when fetching the
        individual product page and still processes the variant data it has.
        """
        # --- Arrange ---
        mock_search_response = MagicMock()
        mock_search_response.text = SEARCH_RESULTS_HTML

        # First call (search) succeeds, second call (product page) fails.
        mock_make_request.side_effect = [mock_search_response, None]

        # --- Execute ---
        listings = self.scraper._scrape_listings("Test Card")

        # --- Assert ---
        self.assertEqual(len(listings), 2, "Should still find 2 variants even if product page fails")
        # Check that details from the failed page are missing
        self.assertIsNone(listings[0].get('set_code'))
        self.assertIsNone(listings[0].get('collector_number'))
        # Check that details from the variant parsing are still present
        self.assertEqual(listings[0]['price'], 10.00)

    @patch('managers.store_manager.stores.storefronts.crystal_commerce_store._make_request_with_retries')
    def test_scrape_listings_no_variants_found(self, mock_make_request):
        """
        Test that the scraper returns an empty list when a product is found
        but has no 'variants' div.
        """
        # --- Arrange ---
        mock_search_response = MagicMock()
        mock_search_response.text = SEARCH_RESULTS_NO_VARIANTS

        mock_product_response = MagicMock()
        mock_product_response.text = PRODUCT_PAGE_HTML

        mock_make_request.side_effect = [mock_search_response, mock_product_response]

        # --- Execute ---
        listings = self.scraper._scrape_listings("Test Card")

        # --- Assert ---
        self.assertEqual(len(listings), 0, "Should return an empty list if no variants are found")

    def test_parse_variants_handles_malformed_data(self):
        """
        Test that _parse_variants can handle a row with missing price/qty and not crash.
        """
        # --- Arrange ---
        malformed_html = """<div class="product"><div class="variant-row in-stock"><div class="variant-description">Near Mint</div></div></div>"""
        soup = BeautifulSoup(malformed_html, "html.parser")
        product_element = soup.find("div", class_="product")

        # --- Execute & Assert ---
        # The function should run without raising an exception and return an empty list.
        variants = self.scraper._parse_variants(product_element)
        self.assertEqual(variants, [])

    def test_parse_variants_uses_data_price_attribute(self):
        """
        Test that _parse_variants correctly prioritizes the `data-price` attribute
        from the form tag over the text in the price span.
        """
        # --- Arrange ---
        soup = BeautifulSoup(SEARCH_RESULTS_WITH_DATA_PRICE, "html.parser")
        product_element = soup.find("li", class_="product")

        # --- Execute ---
        variants = self.scraper._parse_variants(product_element)

        # --- Assert ---
        self.assertEqual(len(variants), 1, "Should find one variant.")
        
        # The price should be from `data-price="$12.34"`, not from `<span class="price">$99.99</span>`.
        self.assertEqual(variants[0]['price'], 12.34, "Price should be parsed from the data-price attribute.")
        self.assertEqual(variants[0]['stock'], 5)
        self.assertEqual(variants[0]['condition'], "Near Mint")


if __name__ == '__main__':
    unittest.main()
