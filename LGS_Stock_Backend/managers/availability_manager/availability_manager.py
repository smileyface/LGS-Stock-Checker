from typing import Dict

# Internal package imports
from . import availability_storage

# Manager package imports
from managers import user_manager
from managers import redis_manager
from managers import socket_manager

# Project package imports
from data import database
from utility import logger


def check_availability(username: str) -> Dict[str, str]:
    """Manually triggers an availability update for a user's card list."""
    logger.info(f"🔄 User {username} requested a manual availability refresh.")
    redis_manager.queue_task("update_wanted_cards_availability", username)
    return {"status": "queued", "message": "Availability update has been triggered."}


def get_card_availability(username):
    user_stores = database.get_user_stores(username)
    user_cards = user_manager.load_card_list(username)

    for store in user_stores:
        if not store or not store.slug:
            continue
        for card in user_cards:
            logger.info(f"🔍 Checking availability for {card.card_name} at {store.name}")
            cached_data = availability_storage.get_availability_data(store.slug, card.card_name)
            if cached_data is None:
                # Fetch availability for the specific card at the store
                # Pass the store's slug and the card as a dictionary
                redis_manager.queue_task("managers.tasks_manager.availability_tasks.update_availability_single_card",
                                         username, store.slug, card.model_dump())
                    # Immediately notify the client that a check has been queued for this specific card.
                # This allows the UI to show a "checking..." state for the individual item.
                socket_manager.socketio.emit(
                    "availability_check_started",
                    {"store": store.name, "card": card.card_name},
                    room=username,
                )
                logger.info(f"⏳ Queued availability check for {card.card_name} at {store.name}.")
            else:
                logger.info(f"✅ Availability data for {card.card_name} at {store.name} is already cached.")
                socket_manager.socket_emit.emit_card_availability_data(username, store.name, card.card_name, cached_data)
    return {"status": "processing", "message": "Availability check initiated. Cached data sent; new data is being fetched."}
