from typing import Dict
from data import database
from managers import user_manager
from managers import redis_manager
from managers import socket_manager
from . import availability_storage
from utility.logger import logger


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
            else:
                logger.info(f"✅ Availability data for {card.card_name} at {store.name} is already cached.")
                socket_manager.socket_emit.emit_card_availability_data(username, store.name, card.card_name, cached_data)
    return {"status": "completed", "message": "Availability data has been fetched and sent to the UI."}
