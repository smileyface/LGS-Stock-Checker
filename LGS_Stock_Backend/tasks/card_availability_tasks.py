import time

from data import database, cache
from managers import store_manager, user_manager
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
