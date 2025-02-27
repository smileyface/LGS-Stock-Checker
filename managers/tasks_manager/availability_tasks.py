import os
from flask_socketio import SocketIO

from flask import Flask

from managers.availability_manager import get_single_card_availability
from managers.redis_manager import redis_manager, REDIS_URL
from managers.store_manager import STORE_REGISTRY
from managers.user_manager import load_card_list, get_user
from stores.store import Store
from utility.logger import logger


def is_running_in_worker():
    """Detect if the current process is an RQ worker."""
    return os.environ.get("RQ_WORKER") == "1"

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
            redis_manager.queue_task("managers.tasks_manager.availability_tasks.update_availability_single_card",
                                     username, store_name, card)


def update_availability_single_card(username, store_name, card):
    socketio = SocketIO(message_queue=REDIS_URL)
    """Background task to update the availability for a single card at a store."""

    logger.info(f"📌 Task started: Updating availability for {card['card_name']} at {store_name} (User: {username})")

    # Ensure store_name is in the correct format
    if isinstance(store_name, Store):
        store = store_name
        store_name = store_name.store_name  # Extract actual name
        logger.debug(f"🔄 Store provided as object. Using store_name: {store_name}")
    else:
        store = STORE_REGISTRY.get(store_name)
        logger.debug(f"🔍 Retrieved store from STORE_REGISTRY: {store}")

    # Validate store exists
    if not store:
        logger.warning(f"🚨 Store '{store_name}' is not configured or missing from STORE_REGISTRY. Task aborted.")
        return

    card_name = card["card_name"]
    logger.info(f"🔍 Checking availability for {card_name} at {store_name}")

    # Fetch availability using the existing logic
    available_items = get_single_card_availability(username, card, store)

    if available_items:
        logger.info(
            f"✅ Found {len(available_items)} available listings for {card_name} at {store_name}. Caching results...")
    else:
        logger.warning(f"⚠️ No available listings found for {card_name} at {store_name}. Moving on.")
        return

    # Emit WebSocket event to update UI
    logger.info(f"📡 Preparing WebSocket event for {card_name} at {store_name} (User: {username})")
    socketio.emit(
        "card_availability_data",
        {
            "username": username,
            "store": store_name,
            "card": card_name,
            "items": available_items
        },
        namespace="/"
    )
    logger.info(f"✅ WebSocket event sent for {card_name} at {store_name} to user {username}")


