import os
import json
import time
from managers.redis_manager import redis_manager
from core.store_manager import load_store_availability
from managers.user_manager import get_user, get_user_directory, load_card_list, save_json
from utility.logger import logger

# Configurable setting to enable or disable auto-triggering updates
ENABLE_AUTO_TRIGGER = False

def get_wanted_cards():
    """Aggregates all cards that users have in their wanted lists."""
    wanted_cards = set()
    users = get_user("all")  # Assuming this fetches all users
    for user in users:
        user_cards = load_card_list(user["username"])
        for card in user_cards:
            wanted_cards.add(card["card_name"])
    return list(wanted_cards)


def update_wanted_cards_availability():
    """Fetches and caches availability for wanted cards only."""
    wanted_cards = get_wanted_cards()
    logger.info(f"🔄 Updating availability for {len(wanted_cards)} wanted cards.")
    
    availability_update = {}
    for card in wanted_cards:
        availability_update[card] = load_store_availability(card)
        availability_update[card]["last_updated"] = time.time()
    
    previous_availability = load_availability_state("system")
    changes = availability_diff(previous_availability, availability_update)
    
    save_availability_state("system", availability_update)
    redis_manager.store_data("last_availability_update", str(time.time()))
    
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
    redis_manager.schedule_task("update_wanted_cards_availability", 0.5)
    logger.info("⏳ Scheduled wanted card availability updates every 30 minutes.")


# Schedule wanted card updates on startup
queue_wanted_card_updates()
