import requests
import managers.database_manager as database_manager
from bs4 import BeautifulSoup

from utility.logger import logger


class Store:
    """
    Represents a store and provides methods to check card availability.

    Attributes:
        id (int): The unique identifier of the store.
        store_name (str): The name of the store.
        slug (str): The slug identifier for the store.
        homepage (str): The homepage URL of the store.
        search_url (str): The URL used for searching products in the store.
        fetch_strategy (str): The strategy used to fetch data from the store.

    Methods:
        get_search_params(card_name): Returns search parameters for a given card name.
        check_store_availability(soup): Checks the availability of products in the store.
        get_price(soup): Retrieves the price of products from the store.
        get_condition(soup): Retrieves the condition of products from the store.
        get_stock(soup): Retrieves the stock information of products from the store.
        get_product_rows(soup): Retrieves product rows from the store's HTML.
        check_availability(card): Performs the search and checks the availability of the card, with detailed logging.
    """
    def __init__(self, slug):
        store_data = database_manager.get_store_metadata(slug)
        if not store_data:
            raise ValueError(f"Store with slug '{slug}' not found in database.")
        self.id = store_data.id
        self.store_name = store_data.name
        self.slug = store_data.slug
        self.homepage = store_data.homepage
        self.search_url = store_data.search_url
        self.fetch_strategy = store_data.fetch_strategy

    def get_search_params(self, card_name):
        return None

    def check_store_availability(self, soup):
        return None

    def get_price(self, soup):
        return None

    def get_condition(self, soup):
        return None

    def get_stock(self, soup):
        return None

    def get_product_rows(self, soup):
        return None

    def check_availability(self, card):
        """Performs the search and checks the availability of the card, with detailed logging."""
        card_name = ""
        if isinstance(card, str):
            card_name = card
        elif isinstance(card, dict):
            card_name = card['card_name']
        values = []  # List to store valid results

        logger.info(f"🔄 Starting availability check for '{card_name}' at {self.store_name}")

        try:
            # Perform the search
            logger.info(
                f"🔍 Sending request to {self.store_name} with search params: {self.get_search_params(card_name)}")
            response = requests.get(self.search_url, params=self.get_search_params(card_name))

            # Handle server-side issues gracefully
            if response.status_code == 503:
                logger.warning(f"🚨 Service unavailable for {self.store_name}. Retrying later.")
                return []  # Return an empty list to indicate no results

            # Raise an exception for other HTTP errors
            response.raise_for_status()
            logger.info(f"✅ Successfully received response from {self.store_name}")

            # Parse the response HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Fetch and process results from the store's availability checker
            logger.info(f"🔍 Parsing store availability data for '{card_name}'")
            results = self.check_store_availability(soup)

            for result in results:
                # Ensure the result matches the desired card name
                if card_name.lower() in result['name'].lower():
                    values.append(result)

            if values:
                logger.info(f"✅ Found {len(values)} matching listings for '{card_name}' at {self.store_name}")
            else:
                logger.warning(f"🚨 No listings found for '{card_name}' at {self.store_name}")

            return values  # Return all valid results for this card

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error connecting to {self.store_name}: {e}")
            return []  # Return an empty list on connection failure

        except Exception as e:
            logger.error(f"❌ An error occurred while checking availability for '{card_name}': {e}")
            return []  # Return an empty list on any other exception
