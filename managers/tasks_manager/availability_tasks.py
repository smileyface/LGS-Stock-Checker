import os

from flask_socketio import SocketIO

import managers.redis_manager as redis_manager
import managers.store_manager as store_manager
import managers.user_manager as user_manager
from managers import socket_manager, availability_manager
from utility.logger import logger


def is_running_in_worker():
    """Detect if the current process is an RQ worker."""
    return os.environ.get("RQ_WORKER") == "1"


def update_availability(username):
    """
    Background task to enqueue jobs for updating availability, one card at a time.
    """
    # Load the user's card list and selected stores
    card_list = user_manager.load_card_list(username)
    user = user_manager.get_user(username)
    selected_stores = user.get("selected_stores", [])

    if not card_list:
        logger.error(f"❌ No card list found for user: {username}. Task aborted.")
        return

    if not selected_stores:
        logger.error(f"❌ No selected stores found for user: {username}. Task aborted.")
        return

    # Enqueue jobs for each card at each selected store
    for store in selected_stores:
        for card in card_list:
            redis_manager.queue_task("managers.tasks_manager.availability_tasks.update_availability_single_card",
                                     username, store, card)


def update_availability_single_card(username, store_name, card):
    """Background task to update the availability for a single card at a store.
        Emits: WebSocket event to update UI with availability data.
        Caches: Stores card availability data in Redis.
        Returns: True if the task was successful, False otherwise.
    """

    socketio = SocketIO(message_queue=redis_manager.REDIS_URL)

    logger.info(f"📌 Task started: Updating availability for {card['card_name']} at {store_name} (User: {username})")

    # Ensure store_name is in the correct format
    if isinstance(store_name, store_manager.Store):
        store = store_name
        store_name = store_name.store_name  # Extract actual name
        logger.debug(f"🔄 Store provided as object. Using store_name: {store_name}")
    else:
        store = store_manager.store_list(store_name)
        logger.debug(f"🔍 Retrieved store from STORE_REGISTRY: {store}")

    # Validate store exists
    if not store:
        logger.warning(f"🚨 Store '{store_name}' is not configured or missing from STORE_REGISTRY. Task aborted.")
        return False

    card_name = card["card_name"]
    logger.info(f"🔍 Checking availability for {card_name} at {store_name}")

    # Fetch availability using the existing logic
    available_items = store_manager.scrape_store_availability(card_name)

    if available_items:
        logger.info(
            f"✅ Found {len(available_items)} available listings for {card_name} at {store_name}. Caching results...")
    else:
        logger.warning(f"⚠️ No available listings found for {card_name} at {store_name}. Moving on.")
        return True # No results being found is not an error, but no results means no action is needed.

    # Cache availability results
    availability_manager.cache_availability_data(store_name, card_name, available_items)
    logger.info(f"✅ Cached availability results for {card_name} at {store_name}.")

    socket_manager.emit_card_availability_data(username, store_name, card_name, available_items)  # Send WebSocket event
    logger.info(f"✅ WebSocket event sent for {card_name} at {store_name} to user {username}")

    return True

