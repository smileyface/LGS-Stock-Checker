import json
import time

import managers.redis_manager as redis_manager
from managers.store_manager.store_manager import load_store_availability
from managers.user_manager import get_user, load_card_list
from utility.logger import logger

# Configurable setting to enable or disable auto-triggering updates
ENABLE_AUTO_TRIGGER = False


def get_wanted_cards():
    """Aggregates all cards that users have in their wanted lists."""
    logger.info("📌 Starting wanted cards aggregation...")

    wanted_cards = set()
    users = get_user("all")  # Assuming this fetches all users
    logger.info(f"👥 Retrieved {len(users)} users from the database.")

    for user in users:
        username = user["username"]
        logger.info(f"📖 Loading card list for user '{username}'")

        user_cards = load_card_list(username)
        logger.info(f"📦 {username} has {len(user_cards)} cards in their wanted list.")

        for card in user_cards:
            card_name = card["card_name"]
            wanted_cards.add(card_name)
            logger.debug(f"➕ Added '{card_name}' to wanted cards set.")

    logger.info(f"✅ Aggregation complete. Total unique wanted cards: {len(wanted_cards)}")
    return list(wanted_cards)


def load_availability_state(username):
    """Loads availability state for a user from Redis, falling back to JSON if needed."""
    redis_key = f"{username}_availability"

    # Try Redis first
    availability = redis_manager.load_data(redis_key)
    if availability:
        logger.info(f"📥 Loaded availability from Redis for {username}.")
        return json.loads(availability)

    logger.warning(f"⚠️ No availability data found for {username}. Returning empty state.")
    return {}


def save_availability_state(username, availability):
    """Saves availability state in Redis and JSON for persistence."""
    redis_key = f"{username}_availability"
    redis_manager.save_data(redis_key, json.dumps(availability))

    logger.info(f"💾 Availability state saved for {username}.")


def update_wanted_cards_availability(username=None):
    #Fetches and caches availability for wanted cards only.
    if username:
        users = [get_user(username)]  # Fetch only this user
    else:
        users = get_user("all")  # Fetch all users in the background

    wanted_cards = get_wanted_cards()
    logger.info(f"🔄 Updating availability for {len(wanted_cards)} wanted cards.")

    availability_update = {}
    for card in wanted_cards:
        availability_update[card] = load_store_availability(card)
        availability_update[card]["last_updated"] = time.time()

    previous_availability = load_availability_state("system")
    changes = availability_diff(previous_availability, availability_update)

    save_availability_state("system", availability_update)
    redis_manager.save_data("last_availability_update", str(time.time()))

    if changes:
        logger.info("📢 Notifying users of availability changes.")
        notify_users_of_changes(changes)
    else:
        logger.info("✅ No significant changes detected.")


def availability_diff(previous_availability, availability_update):
    """Detects changes in availability and returns a dictionary of differences."""
    changes = {
        "added": {},
        "removed": {},
        "updated": {}
    }

    # Detect removed cards
    for card_name in previous_availability.keys():
        if card_name not in availability_update:
            changes["removed"][card_name] = previous_availability[card_name]

    # Detect new or updated cards
    for card_name, stores in availability_update.items():
        if card_name not in previous_availability:
            changes["added"][card_name] = stores
        else:
            for store, new_listings in stores.items():
                old_listings = previous_availability[card_name].get(store, [])
                if old_listings != new_listings:
                    changes["updated"].setdefault(card_name, {})[store] = {
                        "new": [l for l in new_listings if l not in old_listings],
                        "removed": [l for l in old_listings if l not in new_listings]
                    }
    return changes


def notify_users_of_changes(changes):
    """Logs notifications for users tracking changed cards."""
    for change_type, cards in changes.items():
        for card_name, details in cards.items():
            logger.info(f"🔔 {change_type.upper()} - {card_name}: {details}")


def queue_wanted_card_updates():
    """Queues availability updates every 30 minutes for wanted cards only."""
    redis_manager.schedule_task(update_wanted_cards_availability, 0.5)
    logger.info("⏳ Scheduled wanted card availability updates every 30 minutes.")


# Register function before scheduling
redis_manager.register_function("update_wanted_cards_availability", update_wanted_cards_availability)

# Schedule wanted card updates on startup
queue_wanted_card_updates()
