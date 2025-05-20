from core.set_manager import set_code
from managers.store_manager.stores.store import Store


class Authority_Games_Mesa_Arizona(Store):
    def __init__(self):
        super().__init__("authority_games_mesa_az")

    def get_search_params(self, card_name):
        return {"q": card_name, "c": "1"}

    def check_store_availability(self, soup):
        """Check the availability of all listings for the card."""
        product_rows = self.get_product_rows(soup)
        available_products = []

        for product_row in product_rows:
            try:
                product_type = "unknown"
                if "magic_singles" in soup.prettify():
                    product_type = "magic_single"
                product_price = self.get_price(product_row)
                product_stock = self.get_stock(product_row)
                product_condition = self.get_condition(product_row)
                product_finish = self.get_finish(product_row)
                product_set = self.get_set(product_row)

                available_products.append({
                    "store": self.slug,
                    "price": product_price,
                    "stock": product_stock,
                    "condition": product_condition.split(", ")[0],
                    "finish": product_finish,
                    "set": product_set,
                    "type": product_type
                })
            except Exception as e:
                print(f"Error processing product row: {e}")

        return available_products

    def get_product_rows(self, soup):
        """Find all product rows matching the search query."""
        try:
            products_container = soup.find('ul', class_=['products', 'detailed'])
            if not products_container:
                print(f"{self.store_name} interface is broken")
                return []
            return products_container.find_all('li', class_='product')
        except Exception as e:
            print(f"Error fetching product rows: {e}")
            return []

    def get_price(self, soup):
        try:
            # Extract relevant information from the product
            product_price = soup.find('div', class_='product-price')
            if product_price is not None:
                product_price = product_price.get_text(strip=True)

            return product_price
        except Exception as e:
            print(f"Error getting price: {e}")
            return False

    def get_stock(self, soup):
        try:
            stock_element = soup.find('span', class_='variant-short-info variant-qty')
            return stock_element.get_text(strip=True) if stock_element else '0 In Stock'
        except Exception as e:
            print(f"Error getting stock: {e}")
            return False

    def get_condition(self, soup):
        try:
            condition_element = soup.find('span', class_='variant-short-info variant-description')
            return condition_element.get_text(strip=True) if condition_element else 'Unknown'
        except Exception as e:
            print(f"Error getting condition: {e}")
            return False

    def get_finish(self, soup):
        try:
            product_name = soup.find('h4', class_='name').get_text(strip=True)
            if " - " in product_name:
                return product_name.split(" - ")[1].lower()
            else:
                return "normal"
        except Exception as e:
            print(f"Error processing product row: {e}")

    def get_set(self, soup):
        try:
            condition_element = soup.find('span', class_='category')
            return set_code(condition_element.get_text(strip=True)) if condition_element else 'Unknown'
        except Exception as e:
            print(f"Error getting condition: {e}")
            return False

    def __str__(self):
        return self.store_name
