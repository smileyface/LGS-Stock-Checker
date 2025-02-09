from flask_socketio import emit
from managers.redis_manager import redis_manager
import json

def send_inventory_update(username):
    """
    Fetch the latest inventory state from Redis and send it to the client.
    """
    redis_key = f"{username}_inventory_results"
    inventory = redis_manager.redis_conn.hgetall(redis_key)

    # Convert Redis byte-string response to JSON
    formatted_inventory = {
        key: json.loads(value) for key, value in inventory.items()
    }

    emit("inventory_update", formatted_inventory, broadcast=True)
    print(f"📡 Sent inventory update for {username}")
