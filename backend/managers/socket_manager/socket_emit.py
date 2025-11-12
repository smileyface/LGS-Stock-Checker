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


def emit_from_worker(event: str, data: dict, room: str = None):
    """
    Allows a background worker (which doesn't have the Flask app context)
    to emit a Socket.IO event to clients via the Redis message queue.
    If 'room' is None, it's a broadcast message (e.g., to the server itself).
    """
    target = f"to room '{room}'" if room else "as a broadcast"
    logger.info(f"📢 Worker emitting event '{event}' {target} via Redis.")
    try:
        external_socketio = SocketIO(message_queue=REDIS_URL)
        external_socketio.emit(event, data, room=room)
        logger.info(f"📢 Worker dispatched event '{event}' {target} via Redis.")
    except Exception as e:
        logger.error(
            f"❌ Worker failed to dispatch event '{event}' {target}: {e}"
        )


def emit_card_availability_data(
    username: str, store_slug: str, card_name: str, items: list
):
    """A specific helper for emitting card availability data from a worker."""
    event_data = {"store": store_slug, "card": card_name, "items": items}
    emit_from_worker("card_availability_data", event_data, room=username)
