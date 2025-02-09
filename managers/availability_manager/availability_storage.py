import os
import json
from managers.redis_manager.redis_manager import redis_conn
from utility.logger import logger

def load_availability(username):
    """Loads the availability state for a user from Redis, falling back to JSON."""
    redis_key = f"{username}_availability"
    data = redis_conn.get(redis_key)

    if data:
        logger.info(f"📥 Loaded availability for {username} from Redis.")
        return json.loads(data)

    json_path = os.path.join(get_user_directory(username), "availability.json")
    if os.path.exists(json_path):
        with open(json_path, "r") as file:
            logger.warning(f"⚠️ Redis empty. Loaded availability from JSON for {username}.")
            return json.load(file)

    logger.warning(f"⚠️ No availability data found for {username}.")
    return {}

def save_availability(username, availability):
    """Saves availability data in Redis and JSON as backup."""
    redis_key = f"{username}_availability"
    redis_conn.set(redis_key, json.dumps(availability))

    json_path = os.path.join(get_user_directory(username), "availability.json")
    with open(json_path, "w") as file:
        json.dump(availability, file)

    logger.info(f"💾 Availability data saved for {username}.")
