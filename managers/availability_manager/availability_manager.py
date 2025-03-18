import json

import managers.redis_manager as redis_manager
from managers import database_manager
from managers.store_manager.store_manager import scrape_store_availability, save_store_availability
from utility.logger import logger


def check_availability(username):
    """Manually triggers an availability update for a user's card list."""
    logger.info(f"🔄 User {username} requested a manual availability refresh.")

    redis_manager.queue_task("update_wanted_cards_availability", username)

    return {"status": "queued", "message": "Availability update has been triggered."}


def get_card_availability(username):
    """Fetches a list of user cards that are available in stores."""
    redis_key = f"{username}_availability_results"

    logger.info(f"🔍 Checking cache for availability data: {redis_key}")
    availability_data = redis_manager.get_all_hash_fields(redis_key)  # Fetch all availability data

    if availability_data:
        logger.info(f"✅ Data found in cache for {username}")
    else:
        logger.warning(f"🚨 No cache data found for {username}. Availability check may need store queries.")

    # Convert stored JSON strings back into Python objects
    parsed_data = {key: json.loads(value) for key, value in availability_data.items()} if availability_data else {}

    available_cards = []

    # Load user's wanted cards
    logger.info(f"📖 Loading tracked cards for user: {username}")
    user_cards = database_manager.get_users_cards(username)

    for card in user_cards:
        card_name = card.card_name
        logger.debug(f"🔎 Checking availability for card: {card_name}")

        # Check if this card is available in cache
        stores_with_card = {
            store: listings
            for store, listings in parsed_data.items()
            if store.endswith(f"_{card_name}") and listings  # Ensure there are listings
        }

        # If not found in cache, scrape it!
        if not stores_with_card:
            logger.warning(f"🚨 {card_name} not found in cache. Scraping now.")
            scraped_data = scrape_store_availability(card_name, username)  # 🔥 Trigger scraping

            if scraped_data:
                # Save scraped data to Redis to avoid redundant scraping
                save_store_availability(card_name, scraped_data)
                stores_with_card = scraped_data
                logger.info(f"✅ {card_name} scraped and saved to cache.")

        if stores_with_card:
            logger.info(f"✅ {card_name} found in stores: {list(stores_with_card.keys())}")
            available_cards.append({
                "card_name": card_name,
                "stores": stores_with_card
            })
        else:
            logger.warning(f"🚨 {card_name} still not found in any store after scraping.")

    return available_cards  # Returns a list of available cards
