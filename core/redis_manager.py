import time

import redis
import json
import os

# Detect if running inside Docker or on Windows
if os.getenv("RUNNING_IN_DOCKER"):
    REDIS_HOST = "redis"  # Use "redis" inside Docker
else:
    REDIS_HOST = "localhost"  # Use "localhost" on Windows

REDIS_PORT = 6379
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}"
REFRESH_RATE = 1800  # 30 minutes in seconds

# Initialize Redis connection
redis_conn = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def get_cached_listing(store_name, card_name):
    """Retrieve cached store availability listing if it exists and is not expired."""
    redis_key = f"cache:{store_name}:{card_name}"
    cached_data = redis_conn.get(redis_key)

    if cached_data:
        data = json.loads(cached_data)
        timestamp = data.get("timestamp", 0)

        # If data is fresh, return it; otherwise, return None to trigger a refresh
        if time.time() - timestamp < REFRESH_RATE:
            return data["listings"]

    return None  # Data is stale or missing, trigger a fresh fetch

def cache_listing(store_name, card_name, listings):
    """Cache store availability listing with a timestamp."""
    redis_key = f"cache:{store_name}:{card_name}"
    data = {
        "timestamp": time.time(),
        "listings": listings
    }
    redis_conn.set(redis_key, json.dumps(data))

def save_availability_state(username, availability):
    """
    Saves the availability state for a user to Redis.
    """
    redis_key = f"{username}_availability"
    redis_conn.set(redis_key, json.dumps(availability))
    print(f"✅ Saved availability for {username} to Redis.")

def load_availability_state(username):
    """
    Loads the availability state for a user from Redis.
    """
    redis_key = f"{username}_availability"
    data = redis_conn.get(redis_key)

    if data:
        return json.loads(data)
    print(f"⚠️ No availability found for {username} in Redis.")
    return {}

def delete_availability_state(username):
    """
    Deletes the availability state for a user from Redis.
    """
    redis_key = f"{username}_availability"
    redis_conn.delete(redis_key)
    print(f"🗑 Deleted availability state for {username}.")

def list_all_keys():
    """
    List all keys stored in Redis (for debugging).
    """
    return redis_conn.keys("*")
