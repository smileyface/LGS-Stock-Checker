import json
from typing import Any, Dict, Optional

from managers import redis_manager
from utility import logger


def save_data(key: str, value: Any, field: Optional[str] = None, ex: Optional[int] = None) -> None:
    """
    Save data to Redis with optional expiration.

    - If `field` is provided, uses a Redis hash (`hset`) (no expiration support for hashes).
    - Otherwise, stores the entire `value` as a string (`set`) with optional expiration (`ex`).
    - Logs the action with a timestamp and status.
    """
    try:
        redis_conn = redis_manager.get_redis_connection(decode_responses=True)
        value_json = json.dumps(value)  # Ensure value is serialized

        if field:
            redis_conn.hset(key, field, value_json)
            logger.info(f"💾 Saved data to Redis Hash {key}[{field}] (No Expiration)")
        else:
            if ex:
                redis_conn.set(key, value_json, ex=ex)  # ✅ Now supports expiration!
                logger.info(f"💾 Saved data to Redis Key {key} with expiration: {ex} seconds")
            else:
                redis_conn.set(key, value_json)
                logger.info(f"💾 Saved data to Redis Key {key} (No Expiration)")

    except Exception as e:
        logger.error(f"❌ Error saving data to Redis: {e}")


def load_data(key: str, field: Optional[str] = None) -> Optional[Any]:
    """
    Load data from Redis.
    """
    try:
        redis_conn = redis_manager.get_redis_connection(decode_responses=True)
        data = redis_conn.hget(key, field) if field else redis_conn.get(key)

        if data:
            logger.info(f"🔍 Redis GET [{key}]: {len(data)} bytes")
            return json.loads(data)
        else:
            logger.warning(f"⚠️ Redis key {key} is empty or missing.")
            return None
    except Exception as e:
        logger.error(f"❌ Error loading data from Redis: {e}")
        return None


def get_all_hash_fields(key: str) -> Dict[str, Any]:

    """Retrieve all fields and values from a Redis hash."""
    redis_conn = redis_manager.get_redis_connection(decode_responses=False) # hgetall returns bytes
    data = redis_conn.hgetall(key)
    return {k.decode("utf-8"): json.loads(v) for k, v in data.items()} if data else {}


def delete_data(key: str, field=None) -> None:
    """
    Deletes data from Redis.

    - If `field` is provided, deletes a field from a Redis hash (`hdel`).
    - Otherwise, deletes the entire key (`delete`).
    """
    try:
        redis_conn = redis_manager.get_redis_connection(decode_responses=True)
        if field:
            redis_conn.hdel(key, field)
            logger.info(f"🗑️ Deleted field {field} from Redis Hash {key}")
        else:
            redis_conn.delete(key)
            logger.info(f"🗑️ Deleted Redis Key {key}")

    except Exception as e:
        logger.error(f"❌ Error deleting data from Redis: {e}")
