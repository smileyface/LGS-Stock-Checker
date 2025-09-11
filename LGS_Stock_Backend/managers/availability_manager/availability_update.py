import time

from managers import redis_manager
from data import database
from data import cache
import managers.socket_manager as socket_manager
import managers.store_manager as store_manager
import managers.user_manager as user_manager
from .availability_diff import Changes, detect_changes
from utility import logger

# Configurable setting to enable or disable auto-triggering updates
ENABLE_AUTO_TRIGGER = False


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


def load_availability_state(username: str):
    """Loads availability state for a user from Redis, falling back to JSON if needed."""
    redis_key = f"{username}_availability"

    # Try Redis first
    availability = cache.load_data(redis_key)
    if availability:
        logger.info(f"📥 Loaded availability from Redis for {username}.")
        return availability

    logger.warning(f"⚠️ No availability data found for {username}. Returning empty state.")
    return {}


def save_availability_state(username: str, availability: dict):
    """Saves availability state in Redis."""
    redis_key = f"{username}_availability"
    cache.save_data(redis_key, availability)

    logger.info(f"💾 Availability state saved to Redis for {username}.")


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

    previous_availability = load_availability_state(state_key)
    changes = detect_changes(previous_availability, availability_update)

    save_availability_state(state_key, availability_update)
    cache.save_data("last_availability_update", str(time.time()))

    if changes:
        logger.info(f"📢 Notifying users of availability changes for context '{state_key}'.")
        notify_users_of_changes(changes)
    else:
        logger.info(f"✅ No significant changes detected for context '{state_key}'.")

def notify_users_of_changes(changes: Changes):
    """
    Processes a 'changes' dictionary, finds affected users for each changed card,
    and emits WebSocket notifications to them. This function is designed to be
    called from a background worker.
    """

    added = changes.get("added", {})
    removed = changes.get("removed", {})
    updated = changes.get("updated", {})
    all_changed_cards = set(added.keys()) | set(removed.keys()) | set(updated.keys())

    if not all_changed_cards:
        return

    logger.info(f"📢 Processing notifications for {len(all_changed_cards)} changed cards.")

    # Fetch all affected users for all changed cards in a single database query.
    affected_users_map = database.get_tracking_users_for_cards(list(all_changed_cards))

    for card_name, affected_users in affected_users_map.items():
        if not affected_users:
            logger.debug(f"No users are tracking the changed card '{card_name}'.")
            continue

        # Construct a change summary for this specific card
        card_change_summary = {k: v for k, v in {
            "card_name": card_name, "added": added.get(card_name),
            "removed": removed.get(card_name), "updated": updated.get(card_name),
        }.items() if v is not None}

        for user in affected_users:
            logger.info(f"🔔 Emitting 'availability_changed' to user '{user.username}' for card '{card_name}'.")
            socket_manager.socket_emit.emit_from_worker("availability_changed", card_change_summary, room=user.username)


def queue_wanted_card_updates():
    """Queues availability updates every 30 minutes for wanted cards only."""
    redis_manager.schedule_task(update_wanted_cards_availability, 0.5)
    logger.info("⏳ Scheduled wanted card availability updates every 30 minutes.")
