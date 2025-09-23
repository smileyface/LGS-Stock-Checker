import time

from data import database, cache
from managers import store_manager, user_manager, availability_manager
from managers.socket_manager import socket_emit
from utility import logger


def get_wanted_cards(users: list):
    """Aggregates all cards that users have in their wanted lists."""
    logger.info(f"📌 Starting wanted cards aggregation for {len(users)} user(s)...")

    wanted_cards = set()

    for user in users:
        username = user.username
        if not username:
            continue
        logger.debug(f"📖 Loading card list for user '{username}'")

        user_cards = user_manager.load_card_list(username)

        for card in user_cards:
            card_name = card.card_name
            if not card_name:
                logger.warning(f"❌ Card '{card_name}' in user '{username}' has a null card name. Skipping.")
                continue
            wanted_cards.add(card_name)
            logger.debug(f"➕ Added '{card_name}' to wanted cards set.")

    logger.info(f"✅ Aggregation complete. Total unique wanted cards: {len(wanted_cards)}")
    return list(wanted_cards)


def update_wanted_cards_availability(username=None):
    """
    Fetches and caches availability for wanted cards.
    If a username is provided, it checks only for that user's cards and detects changes against their last known state.
    If no username is provided, it runs a system-wide update for all wanted cards, updating the global 'system' state.
    """
    if username:
        user_obj = database.get_user_by_username(username)  # Use data layer to get the full ORM object
        if not user_obj:
            logger.error(f"Cannot update availability, user '{username}' not found.")
            return
        users = [user_obj]
        state_key = username
    else:
        users = database.get_all_users()
        state_key = "system"

    wanted_cards = get_wanted_cards(users)
    if not wanted_cards:
        logger.info(f"✅ No wanted cards to update for context '{state_key}'. Task complete.")
        return

    logger.info(f"🔄 Updating availability for {len(wanted_cards)} wanted cards.")

    availability_update = {}
    for card in wanted_cards:
        # This function is smart and uses a global cache, so we are not re-scraping unnecessarily.
        availability_update[card] = store_manager.load_store_availability(card)
        availability_update[card]["last_updated"] = time.time()


def update_availability_single_card(username, store_name, card):
    """Background task to update the availability for a single card at a store.
    """
    # Validate store_name
    if not store_name:
        logger.warning(f"🚨 Invalid store name: {store_name}. Task aborted.")
        return False

    card_name = card.get("card_name")
    if not card_name:
        logger.error(f"❌ Task received card data without a 'card_name'. Aborting. Data: {card}")
        return False

    logger.info(f"📌 Task started: Updating availability for {card_name} at {store_name} (User: {username})")

    # Ensure store_name is in the correct format
    store = store_manager.store_list(store_name)
    if not store:
        logger.warning(f"🚨 Store '{store_name}' is not configured or missing from STORE_REGISTRY. Task aborted.")
        return False

    logger.info(f"🔍 Checking availability for {card_name} at {store_name}")

    # Fetch availability using the specific store's implementation
    card_specs = card.get("specifications")
    available_items = store.fetch_card_availability(card_name, card_specs)

    if available_items:
        logger.info(f"✅ Found {len(available_items)} listings for {card_name} at {store_name}. Caching and emitting.")
        
        # 1. Cache the results first for data integrity.
        availability_manager.cache_availability_data(store_name, card_name, available_items)
        logger.info(f"✅ Cached availability results for {card_name} at {store_name}.")

        # 2. Use the dedicated worker-safe emit function from socket_emit.
        event_data = {"username": username, "store": store_name, "card": card_name, "items": available_items}
        socket_emit.emit_from_worker("card_availability_data", event_data, room=username)
    else:
        logger.warning(f"⚠️ No available listings found for {card_name} at {store_name}. Moving on.")

    return True
