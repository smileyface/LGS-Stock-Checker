import requests
from bs4 import BeautifulSoup


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

        try:
            # Perform the search
            response = requests.get(self.search_url, params=self.get_search_params(card_name))

            # Handle server-side issues gracefully
            if response.status_code == 503:
                print(f"Service unavailable for {self.store_name}. Retrying later.")
                return []  # Return an empty list to indicate no results

            # Raise an exception for other HTTP errors
            response.raise_for_status()

            # Parse the response HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Fetch and process results from the store's availability checker
            results = self.check_store_availability(soup)
            for result in results:
                # Ensure the result matches the desired card name
                if card_name.lower() in result['name'].lower():
                    values.append(result)

            return values  # Return all valid results for this card

        except requests.exceptions.RequestException as e:
            print(f"Error connecting to {self.store_name}: {e}")
            return []  # Return an empty list on connection failure

        except Exception as e:
            print(f"An error occurred while checking availability for {card_name}: {e}")
            return []  # Return an empty list on any other exception

