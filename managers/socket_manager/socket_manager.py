from flask_socketio import SocketIO, emit
from flask import request
from managers.redis_manager.redis_manager import redis_conn, REDIS_URL
import json

# Initialize Flask-SocketIO
socketio = SocketIO(
    message_queue=REDIS_URL,
    cors_allowed_origins="*",
    async_mode="eventlet"
)

# Store active WebSocket connections
connected_clients = set()

# 🔹 WebSocket Connection Handling
from managers.socket_manager.socket_connections import handle_connect, handle_disconnect

# 🔹 WebSocket Event Handling
from managers.socket_manager.socket_events import send_inventory_update
