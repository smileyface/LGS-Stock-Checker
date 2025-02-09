import os
from managers.availability_manager.availability_storage import load_availability, save_availability
from managers.availability_manager.availability_diff import detect_changes
from managers.redis_manager import redis_manager
from utility.logger import logger

def check_availability(username):
    """Manually triggers an availability update for a user's card list."""
    logger.info(f"🔄 User {username} requested a manual availability refresh.")

    redis_manager.queue_task("update_wanted_cards_availability", username)

    return {"status": "queued", "message": "Availability update has been triggered."}
