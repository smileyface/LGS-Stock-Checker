import json

from managers.redis_manager.redis_manager import redis_conn
from utility.logger import logger

SCRYFALL_CARD_CACHE_KEY = "scryfall_card_names"
SCRYFALL_CARD_CACHE_EXPIRY = 86400


def save_data(key, value, field=None):
    """
    Save data to Redis.

    - If `field` is provided, uses a Redis hash (`hset`).
    - Otherwise, stores the entire `value` as a string (`set`).
    """
    try:
        value_json = json.dumps(value)  # Ensure value is serialized

        if field:
            redis_conn.hset(key, field, value_json)
            logger.info(f"💾 Saved data to Redis Hash {key}[{field}]")
        else:
            redis_conn.set(key, value_json)
            logger.info(f"💾 Saved data to Redis Key {key}")

    except Exception as e:
        logger.error(f"❌ Error saving data to Redis: {e}")


def load_data(key, field=None):
    """
    Load data from Redis.
    """
    try:
        if field:
            data = redis_conn.hget(key, field)
            logger.info(f"🔍 Redis HGET [{key}][{field}]: {len(data)}")
            if data:
                return json.loads(data)
            else:
                return None
        else:
            data = redis_conn.get(key)
            logger.info(f"🔍 Redis GET [{key}]: {len(data)}")
            if data:
                return json.loads(data)
            else:
                logger.warning(f"⚠️ Redis key {key} is empty or missing.")
                return None
    except Exception as e:
        logger.error(f"❌ Error loading data from Redis: {e}")
        return None


def get_all_hash_fields(key):
    """Retrieve all fields and values from a Redis hash."""
    data = redis_conn.hgetall(key)
    return {k.decode("utf-8"): json.loads(v) for k, v in data.items()} if data else {}


def delete_data(key, field=None):
    """
    Deletes data from Redis.

    - If `field` is provided, deletes a field from a Redis hash (`hdel`).
    - Otherwise, deletes the entire key (`delete`).
    """
    try:
        if field:
            redis_conn.hdel(key, field)
            logger.info(f"🗑️ Deleted field {field} from Redis Hash {key}")
        else:
            redis_conn.delete(key)
            logger.info(f"🗑️ Deleted Redis Key {key}")

    except Exception as e:
        logger.error(f"❌ Error deleting data from Redis: {e}")
