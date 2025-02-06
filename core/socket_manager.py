from flask_socketio import SocketIO, emit
from flask import request
from core.redis_manager import redis_conn, REDIS_URL
import json
import os


# Initialize Flask-SocketIO
socketio = SocketIO(
    message_queue=REDIS_URL,
    cors_allowed_origins="*",
    async_mode="eventlet"
)

# Store active WebSocket connections
connected_clients = set()


@socketio.on("connect")
def handle_connect():
    """Handle new WebSocket connections."""
    print(f"🟢 Client connected: {request.sid}")
    connected_clients.add(request.sid)


@socketio.on("disconnect")
def handle_disconnect():
    """Handle WebSocket disconnections."""
    print(f"🔴 Client disconnected: {request.sid}")
    connected_clients.discard(request.sid)


@socketio.on("request_inventory_update")
def send_inventory_update(username):
    """
    Fetch the latest inventory state from Redis and send it to the client.
    """
    redis_key = f"{username}_inventory_results"
    inventory = redis_conn.hgetall(redis_key)

    # Convert Redis byte-string response to JSON
    formatted_inventory = {
        key: json.loads(value) for key, value in inventory.items()
    }

    emit("inventory_update", formatted_inventory, broadcast=True)
    print(f"📡 Sent inventory update for {username}")
