import json
import time
import managers.redis_manager as redis_manager
import managers.socket_manager as socket_manager
import managers.database_manager as database_manager
from managers.store_manager.stores import store_list  # Assuming this is your base store scraper
from utility.logger import logger

CACHE_EXPIRATION = 1800  # 30 minutes in seconds


def load_store_availability(card_name, username):
    """Loads availability data for a card from Redis storage, scraping if needed."""
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


def scrape_store_availability(card_name, username):
    """Scrapes only the stores selected by the user for a given card with detailed logging."""
    logger.info(f"🔄 Starting availability check for '{card_name}' requested by {username}")

    scraped_data = {}

    # Fetch user's selected stores
    user_stores = database_manager.get_user_stores(username)
    logger.info(f"📥 Retrieved {len(user_stores)} stores selected by user '{username}'.")

    # Get actual store classes from store manager
    store_classes = store_list(user_stores)
    logger.info(f"📂 Found {len(store_classes)} matching store scrapers.")

    for store_class in store_classes:
        try:
            store_instance = store_class()  # Instantiate store class
            store_name = store_class.slug
            logger.info(f"🔍 Scraping '{store_name}' for card: {card_name}")

            store_listings = store_instance.check_store_availability(card_name)

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


def save_store_availability(card_name, listings):
    """Saves scraped store availability to Redis with a 30-minute expiration."""
    redis_key = f"store_availability_{card_name}"
    redis_manager.save_data(redis_key, json.dumps(listings), ex=CACHE_EXPIRATION)  # ✅ Store with expiration
