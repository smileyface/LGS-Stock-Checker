"""
Unit tests for the CrystalCommerceStore base class.
"""
import unittest
from unittest.mock import patch, MagicMock
import requests
from LGS_Stock_Backend.managers.store_manager.stores.storefronts.crystal_commerce_store import CrystalCommerceStore

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

class TestCrystalCommerceStore(unittest.TestCase):
    """Tests for the CrystalCommerceStore base scraper."""
    def setUp(self):
        """Set up the test case."""
        # Instantiate the base class directly for testing its logic
        self.scraper = CrystalCommerceStore(
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

    @patch('LGS_Stock_Backend.managers.store_manager.stores.storefronts.crystal_commerce_store.requests.get')
    @patch('LGS_Stock_Backend.managers.store_manager.stores.storefronts.crystal_commerce_store.set_code')
    def test_scrape_listings_success(self, mock_set_code, mock_get):
        """
        Test the full scraping process for a card, mocking both network calls.
        """
        # Configure the mock to use our side_effect function
        mock_get.side_effect = self.mock_requests_get
        # Configure mock_set_code to return the expected 'tst' for any input
        mock_set_code.return_value = "tst"
        
        # --- Execute ---
        card_name = "Test Card"
        listings = self.scraper._scrape_listings(card_name)

        # --- Assert ---
        self.assertEqual(len(listings), 2, "Should find two listings (one regular, one foil)")

        # Verify the first listing (Non-Foil)
        listing1 = listings[0]
        self.assertEqual(listing1['name'], "Test Card")
        self.assertEqual(listing1['price'], 10.00)
        self.assertEqual(listing1['stock'], 2)
        self.assertEqual(listing1['condition'], "Near Mint")
        self.assertEqual(listing1['finish'], "non-foil")
        self.assertEqual(listing1['set_code'], "tst")
        self.assertEqual(listing1['collector_number'], "123")
        self.assertIn("/products/1234-test-card", listing1['url'])

        # Verify the second listing (Foil)
        listing2 = listings[1]
        self.assertEqual(listing2['name'], "Test Card")
        self.assertEqual(listing2['price'], 25.00)
        self.assertEqual(listing2['stock'], 1)
        self.assertEqual(listing2['condition'], "Near Mint")
        self.assertEqual(listing2['finish'], "foil")
        self.assertEqual(listing2['collector_number'], "123") # Both variants share the collector number

        # Verify that requests.get was called correctly
        self.assertEqual(mock_get.call_count, 2, "Should make one call for search and one for the product page")
        
        # Check the first call (search)
        search_call_args = mock_get.call_args_list[0]
        self.assertEqual(search_call_args.kwargs['params'], {'q': 'Test Card', 'c': 1})
        
        # Check the second call (product page)
        product_page_call_args = mock_get.call_args_list[1]
        self.assertIn('/products/1234-test-card', product_page_call_args.args[0])
        
        # Verify that set_code was called with the correct set name from the HTML
        mock_set_code.assert_called_with("Magic The Gathering: Test Set")

    @patch('LGS_Stock_Backend.managers.store_manager.stores.storefronts.crystal_commerce_store.requests.get')
    @patch('LGS_Stock_Backend.managers.store_manager.stores.storefronts.crystal_commerce_store.set_code')
    def test_scrape_listings_deduplicates_results(self, mock_set_code, mock_get):
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
        mock_get.side_effect = [mock_search_response, mock_product_response]
        mock_set_code.return_value = "tst"

        # --- Execute ---
        card_name = "Test Card"
        listings = self.scraper._scrape_listings(card_name)

        # --- Assert ---
        # The source HTML has 3 variants, but 2 are identical.
        # The scraper should return only 2 unique listings.
        self.assertEqual(len(listings), 2, "Should find 2 unique listings after deduplication")

    @patch('LGS_Stock_Backend.managers.store_manager.stores.storefronts.crystal_commerce_store.requests.get')
    @patch('LGS_Stock_Backend.managers.store_manager.stores.storefronts.crystal_commerce_store.set_code')
    def test_scrape_listings_stops_on_non_matching_card(self, mock_set_code, mock_get):
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
        mock_get.side_effect = [mock_search_response, mock_product_response]
        mock_set_code.return_value = "tst"

        # --- Execute ---
        card_name = "Test Card"
        listings = self.scraper._scrape_listings(card_name)

        # --- Assert ---
        # It should only find the one listing from the first product.
        self.assertEqual(len(listings), 1, "Should only process listings before the non-matching card")

        # It should have made one call for the search page and one for the first product page.
        # It should NOT have made a call for the second "Test Card" after the "Wrong Card".
        self.assertEqual(mock_get.call_count, 2, "Should stop making requests after a non-match")

    @patch('LGS_Stock_Backend.managers.store_manager.stores.storefronts.crystal_commerce_store.logger')
    @patch('LGS_Stock_Backend.managers.store_manager.stores.storefronts.crystal_commerce_store.requests.get')
    def test_scrape_listings_search_network_failure(self, mock_get, mock_logger):
        """
        Test that _scrape_listings handles a network error during the initial search
        and returns an empty list without crashing.
        """
        # --- Arrange ---
        # Configure the mock to raise a RequestException, simulating a network failure.
        mock_get.side_effect = requests.exceptions.RequestException("Network error")
        card_name = "Test Card"

        # --- Execute ---
        listings = self.scraper._scrape_listings(card_name)

        # --- Assert ---
        # 1. The function should return an empty list.
        self.assertEqual(listings, [])

        # 2. An error should have been logged.
        mock_logger.error.assert_called_once()
        self.assertIn("Failed to fetch search results", mock_logger.error.call_args[0][0])


if __name__ == '__main__':
    unittest.main()
