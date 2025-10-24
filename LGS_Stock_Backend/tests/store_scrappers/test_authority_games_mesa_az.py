import unittest
from unittest.mock import patch, MagicMock
import requests
from managers.store_manager.stores.authority_games_mesa_az import Authority_Games_Mesa_Arizona

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
<div class="product-details">
    <div class="card-number">
        <a href="/products/search?collector_number=123">123/456</a>
    </div>
</div>
"""

class TestAuthorityGamesMesaArizona(unittest.TestCase):
    def setUp(self):
        """Set up the test case."""
        self.scraper = Authority_Games_Mesa_Arizona()

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

    @patch('managers.store_manager.stores.authority_games_mesa_az.requests.get')
    @patch('managers.store_manager.stores.authority_games_mesa_az.set_code')
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
        self.assertEqual(listing1['set'], "tst") # Assuming set_code maps 'Test Set' to 'tst'
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

    @patch('managers.store_manager.stores.authority_games_mesa_az.logger')
    @patch('managers.store_manager.stores.authority_games_mesa_az.requests.get')
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
