"""
This module centralizes all Socket.IO emission logic, providing helper
functions for sending messages from both the main Flask app and from
background RQ workers.
"""

from flask_socketio import SocketIO

from utility import logger
from .socket_manager import socketio
from managers.redis_manager import REDIS_URL
from schema.messaging import messages


def log_and_emit(level: str, message: str, room: str = ""):
    """Logs a message and emits it to a specific room or all clients."""
    logger.info(f"📢 {level.upper()}: {message}")
    payload = {"level": level.upper(), "message": message}
    if room:
        socketio.emit("server_log", payload, to=room)
    else:
        socketio.emit("server_log", payload)


def emit_from_worker(event: str, data: dict, room: str = ""):
    """
    Allows a background worker (which doesn't have the Flask app context)
    to emit a Socket.IO event to clients via the Redis message queue.
    If 'room' is None, it's a broadcast message (e.g., to the server itself).
    """
    target = f"to room '{room}'" if room else "as a broadcast"
    logger.info(f"📢 Worker emitting event '{event}' {target} via Redis.")
    try:
        external_socketio = SocketIO(message_queue=REDIS_URL)
        external_socketio.emit(event, data, to=room)
        logger.info(f"📢 Worker dispatched event '{event}' {target} via Redis.")
    except Exception as e:
        logger.error(f"❌ Worker failed to dispatch event '{event}' {target}: {e}")


def emit_message(message: messages.APIMessageResponses, room: str = "") -> None:
    target = f"to room '{room}'" if room else "as a broadcast"
    logger.info(f"📢 Server emitting message '{message.name}' {target}.")
    socketio.emit(message.name, message.model_dump(), to=room)
    logger.info(f"📢 Server dispatched message '{message.name}' {target}.")
