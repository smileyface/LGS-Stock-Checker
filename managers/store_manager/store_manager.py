import json
import time
from typing import Any
from typing import Dict

import managers.database_manager as database_manager
import managers.redis_manager as redis_manager
from managers.store_manager.stores import store_list  # Assuming this is your base store scraper
from utility.logger import logger

CACHE_EXPIRATION = 1800  # 30 minutes in seconds


def load_store_availability(card_name: str, username: str) -> Dict:
    """Retrieve availability data for a specified card from Redis cache or scrape it if not cached.

    Args:
        card_name (str): The name of the card to check availability for.
        username (str): The username of the person requesting the availability check.
    
    Returns:
        dict: A dictionary containing availability data if found, otherwise an empty dictionary.
    """
    redis_key = f"store_availability_{card_name}"
    cached_data = redis_manager.load_data(redis_key)

    if cached_data:
        return json.loads(cached_data)  # ✅ Return cached data if found

    # 🚨 Cache miss: Scrape the store websites
    scraped_data = scrape_store_availability(card_name, username)

    if scraped_data:
        save_store_availability(card_name, scraped_data)  # Save the scraped data
        return scraped_data

    return {}  # Return empty if nothing was found


def scrape_store_availability(card_name: str, username: str) -> Dict[str, Any]:
    """
    Scrape availability of a specified card from user-selected stores.
    
    This function retrieves the stores selected by the user, instantiates
    the corresponding store classes, and checks the availability of the
    specified card in each store. Detailed logging is performed throughout
    the process to track the progress and any issues encountered.
    
    Args:
        card_name (str): The name of the card to check availability for.
        username (str): The username of the user whose selected stores will be scraped.
    
    Returns:
        dict: A dictionary containing the scraped data with store names as keys
        and their respective listings and last updated timestamps as values.
    """
    logger.info(f"🔄 Starting availability check for '{card_name}' requested by {username}")

    scraped_data = {}

    # Fetch user's selected stores
    user_stores = database_manager.get_user_stores(username)
    logger.info(f"📥 Retrieved {len(user_stores)} stores selected by user '{username}'.")

    # Get actual store classes from store manager
    store_classes = store_list(user_stores)
    logger.info(f"📂 Found {len(store_classes)} matching store scrapers.")

    for store_class in store_classes:
        store_instance = store_class()  # Instantiate store class
        store_name = store_instance.slug

        logger.info(f"🔍 Scraping '{store_name}' for card: {card_name}")
        try:
            store_listings = store_instance.check_availability(card_name)

            if store_listings:
                scraped_data[store_name] = {
                    "listings": store_listings,
                    "last_updated": time.time(),
                }
                logger.info(f"✅ Scraping successful for '{store_name}'. Found {len(store_listings)} listings.")
            else:
                logger.warning(f"🚨 '{store_name}' returned no listings for '{card_name}'.")

        except Exception as e:
            logger.error(f"❌ Error scraping '{store_name}': {e}")

    if scraped_data:
        logger.info(f"💾 Successfully scraped availability for '{card_name}'. Saving results.")
    else:
        logger.warning(f"🚨 No data scraped for '{card_name}'. Stores may be empty or failing.")

    return scraped_data


def save_store_availability(card_name: str, listings: Dict) -> None:
    """
    Saves the availability of a store's card listings to Redis.
    
    Parameters:
        card_name (str): The name of the card for which availability is being saved.
        listings (dict): A list of store availability data for the specified card.
    
    The data is stored with a key prefixed by 'store_availability_' and expires after 30 minutes.
    """
    redis_key = f"store_availability_{card_name}"
    redis_manager.save_data(redis_key, json.dumps(listings), ex=CACHE_EXPIRATION)  # ✅ Store with expiration
