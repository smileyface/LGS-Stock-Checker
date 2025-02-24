import requests
from bs4 import BeautifulSoup

from utility.logger import logger


class Store:
    def __init__(self):
        self.homepage = ""
        self.search_url = ""
        self.store_name = ""

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
        """Performs the search and checks the availability of the card."""
        card_name = card['card_name']
        values = []  # List to store valid results

        logger.info(f"🔍 Checking availability for '{card_name}' at {self.store_name}")

        try:
            # Perform the search
            response = requests.get(self.search_url, params=self.get_search_params(card_name))

            # Handle server-side issues gracefully
            if response.status_code == 503:
                logger.warning(f"🚨 {self.store_name} is currently unavailable (503). Retrying later.")
                return []  # Return an empty list to indicate no results

            # Raise an exception for other HTTP errors
            response.raise_for_status()

            # Parse the response HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Fetch and process results from the store's availability checker
            results = self.check_store_availability(soup)

            if not results:
                logger.info(f"❌ No results found for '{card_name}' at {self.store_name}.")
                return [] #return an empty list if no cards are found
            else:
                logger.info(f"✅ Found {len(results)} results for '{card_name}' at {self.store_name}.")

            for result in results:
                # Ensure the result matches the desired card name
                if card_name.lower() in result['name'].lower():
                    values.append(result)

            if values:
                logger.info(f"📌 {len(values)} valid listings found for '{card_name}' at {self.store_name}.")
            else:
                logger.info(f"⚠️ No exact matches for '{card_name}' at {self.store_name}.")

            return values  # Return all valid results for this card

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error connecting to {self.store_name} while searching for '{card_name}': {e}")
            return []  # Return an empty list on connection failure

        except Exception as e:
            logger.error(f"🚨 Unexpected error while checking '{card_name}' at {self.store_name}: {e}")
            return []  # Return an empty list on any other exception


