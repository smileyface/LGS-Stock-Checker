from flask_socketio import SocketIO, emit
from flask import request
from managers.redis_manager.redis_manager import REDIS_URL
from utility.logger import logger
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
from managers.socket_manager.socket_handlers import handle_get_cards, handle_get_card_availability, handle_save_cards, handle_parse_card_list


def log_and_emit(level, message):
    """Logs to the backend logger and emits to the front end."""
    if level == "info":
        logger.info(message)
    elif level == "warning":
        logger.warning(message)
    elif level == "error":
        logger.error(message)

    # Emit log to frontend
    socketio.emit("server_log", {"level": level.upper(), "message": message})


def register_socket_events(socketio: SocketIO):
    """Registers all WebSocket event handlers."""

    socketio.on_event("connect", handle_connect)
    socketio.on_event("get_cards", handle_get_cards)
    socketio.on_event("get_card_availability", handle_get_card_availability)
    socketio.on_event("save_cards", handle_save_cards)
    socketio.on_event("parse_card_list", handle_parse_card_list)