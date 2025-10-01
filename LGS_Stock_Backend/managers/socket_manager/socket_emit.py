"""
This module centralizes all Socket.IO emission logic, providing helper
functions for sending messages from both the main Flask app and from
background RQ workers.
"""
from flask_socketio import SocketIO

from utility import logger
from .socket_manager import socketio
from managers.redis_manager import REDIS_URL


def log_and_emit(level: str, message: str, room: str = None):
    """Logs a message and emits it to a specific room or all clients."""
    logger.info(f"📢 {level.upper()}: {message}")
    payload = {"level": level.upper(), "message": message}
    if room:
        socketio.emit("server_log", payload, room=room)
    else:
        socketio.emit("server_log", payload)


def emit_from_worker(event: str, data: dict, room: str):
    """
    Allows a background worker (which doesn't have the Flask app context)
    to emit a Socket.IO event to clients via the Redis message queue.
    """
    try:
        # Create a new SocketIO instance that only knows about the message queue.
        # This is the correct way for external processes to publish events.
        external_socketio = SocketIO(message_queue=REDIS_URL)
        external_socketio.emit(event, data, room=room)
        logger.info(f"📢 Worker dispatched event '{event}' to room '{room}' via Redis.")
    except Exception as e:
        logger.error(f"❌ Worker failed to dispatch event '{event}' to room '{room}': {e}")


def emit_card_availability_data(username: str, store_slug: str, card_name: str, items: list):
    """A specific helper for emitting card availability data from a worker."""
    event_data = {"store": store_slug, "card": card_name, "items": items}
    emit_from_worker("card_availability_data", event_data, room=username)