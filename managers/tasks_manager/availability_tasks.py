from managers.availability_manager import get_single_card_availability
from managers.redis_manager import redis_manager
from managers.extensions import socketio
from managers.store_manager import store_availability_in_cache, STORE_REGISTRY
from managers.user_manager import load_card_list, get_user
from utility.logger import logger


def update_availability(username):
    """
    Background task to enqueue jobs for updating availability, one card at a time.
    """
    # Load the user's card list and selected stores
    card_list = load_card_list(username)
    user = get_user(username)
    selected_stores = user.get("selected_stores", [])

    for store_name in selected_stores:
        for card in card_list:
            redis_manager.queue_task("update_availability_single_card", username, store_name, card)


def update_availability_single_card(username, store_name, card):
    """Background task to update the availability for a single card at a store."""
    store = STORE_REGISTRY.get(store_name)
    if not store:
        logger.warning(f"🚨 Store '{store_name}' is not configured.")
        return

    card_name = card["card_name"]

    # Fetch availability using the existing logic
    available_items = get_single_card_availability(card, store)

    # Cache the results
    store_availability_in_cache(card_name, store_name, available_items)

    # Emit WebSocket event to update UI
    socketio.emit(
        "availability_update",
        {
            "username": username,
            "store": store_name,
            "card": card_name,
            "items": available_items
        },
        namespace="/"
    )

    logger.info(f"✅ Updated availability for {card_name} at {store_name}. WebSocket event sent.")
