import json
from managers.redis_manager import redis_manager
from managers.store_manager import STORE_REGISTRY
from managers.user_manager import load_card_list, get_user
from managers.socket_manager import socketio
from managers.store_manager import save_store_availability
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
    """Background task to update the availability for a single card."""
    store = STORE_REGISTRY.get(store_name)
    if not store:
        logger.warning(f"🚨 Store '{store_name}' is not configured.")
        return

    card_name = card["card_name"]
    available_items = store.fetch_card_availability(card_name)

    # Save results to the store's persistent cache
    save_store_availability(store_name, card_name, available_items)

    # Save to Redis under user availability
    redis_key = f"{username}_availability_results"
    redis_manager.save_data(redis_key, f"{store_name}_{card_name}", json.dumps(available_items))

    # Emit WebSocket event to update UI
    socketio.emit(
        "availability_update",
        {"username": username, "store": store_name, "card": card_name, "items": available_items},
        namespace="/",
    )

    logger.info(f"✅ Availability updated for {card_name} at {store_name}. WebSocket event sent.")
