from data import database
from data import cache
import managers.socket_manager as socket_manager
from .availability_diff import Changes, detect_changes
from utility import logger

# Configurable setting to enable or disable auto-triggering updates
ENABLE_AUTO_TRIGGER = False


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
            socket_manager.emit_from_worker("availability_changed", card_change_summary, room=user.username)
