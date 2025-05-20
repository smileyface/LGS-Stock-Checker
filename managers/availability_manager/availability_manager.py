from typing import Dict

import managers.database_manager as database_manager
import managers.redis_manager as redis_manager
import managers.socket_manager as socket_manager
from managers.availability_manager import availability_storage
from utility.logger import logger


def check_availability(username: str) -> Dict[str, str]:
    """Manually triggers an availability update for a user's card list."""
    logger.info(f"🔄 User {username} requested a manual availability refresh.")
    redis_manager.queue_task("update_wanted_cards_availability", username)
    return {"status": "queued", "message": "Availability update has been triggered."}


def get_card_availability(username):
    user_stores = database_manager.get_user_stores(username)
    user_cards = database_manager.get_users_cards(username)

    for store in user_stores:
        for card in user_cards:
            logger.info(f"🔍 Checking availability for {card['card_name']} at {store}")
            data = availability_storage.get_availability_data(store, card["card_name"])
            if data is None:
                # Fetch availability for the specific card at the store
                redis_manager.queue_task("managers.tasks_manager.availability_tasks.update_availability_single_card",
                                         username, store, card)
            else:
                logger.info(f"✅ Availability data for {card['card_name']} at {store} is already cached.")
                socket_manager.emit_card_availability_data(username, store, card["card_name"],
                                                           data)
    return {"status": "completed", "message": "Availability data has been fetched and sent to the UI."}
