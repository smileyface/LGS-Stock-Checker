import json

from managers.redis_manager import redis_manager
from utility.logger import logger


def load_availability(username):
    """Loads the availability state for a user from Redis, falling back to JSON."""
    redis_key = f"{username}_availability"
    data = redis_manager.load_data(redis_key)

    if data:
        logger.info(f"📥 Loaded availability for {username} from Redis.")
        return json.loads(data)

    logger.warning(f"⚠️ No availability data found for {username}.")
    return {}

def save_availability(username, availability):
    """Saves availability data in Redis and JSON as backup."""
    redis_key = f"{username}_availability"
    redis_manager.save_data(redis_key, json.dumps(availability))

    logger.info(f"💾 Availability data saved for {username}.")
