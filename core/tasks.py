import json

from rq import Queue

from core.redis_manager import redis_conn, get_cached_listing, cache_listing
from core.store_manager import STORE_REGISTRY
from core.user_manager import load_card_list, get_user

from core.socket_manager import socketio



def update_availability(username):
    """
    Background task to enqueue jobs for updating availability, one card at a time.
    """
    # Connect to Redis
    queue = Queue(connection=redis_conn)

    # Load the user's card list and selected stores
    card_list = load_card_list(username)
    user = get_user(username)
    selected_stores = user.get("selected_stores", [])

    for store_name in selected_stores:
        for card in card_list:
            # Enqueue a job for each card in the list
            queue.enqueue("core.tasks.update_availability_single_card", username, store_name, card)
            print(f"Enqueued job for {card['card_name']} at {store_name}.")



def update_availability_single_card(username, store_name, card):
    """Background task to update the availability for a single card."""
    store = STORE_REGISTRY.get(store_name)
    if not store:
        print(f"Store '{store_name}' is not configured.")
        return

    card_name = card["card_name"]

    # Save results to the store's persistent cache
    save_store_availability(store_name, card["card_name"], available_items)

    # Save to Redis under user availability
    redis_key = f"{username}_availability_results"
    redis_conn.hset(redis_key, f"{store_name}_{card_name}", json.dumps(available_items))

    # Emit WebSocket event to update UI
    socketio.emit(
        "availability_update",
        {"username": username, "store": store_name, "card": card_name, "items": available_items},
        namespace="/",
    )

    print(f"✅ availability updated for {card} at {store_name}. WebSocket event sent.")
