from flask_socketio import SocketIO

import managers.redis_manager as redis_manager
from managers.socket_manager.socket_manager import socketio
from utility.logger import logger


def emit_card_availability_data(username, store_name, card_name, items):
    """Emits card availability data to a specific user via the main server's socketio instance."""
    logger.info(f"📡 Emitting card availability for {card_name} at {store_name} to user {username}")
    event_data = {
        "username": username,
        "store": store_name,
        "card": card_name,
        "items": items
    }
    # Use rooms for targeted emits, which is more reliable than managing SIDs.
    socketio.emit("card_availability_data", event_data, room=username)


def log_and_emit(level: str, message: str):
    """Logs to the backend logger and emits a log event to all connected clients."""
    if level == "info":
        logger.info(message)
    elif level == "warning":
        logger.warning(message)
    elif level == "error":
        logger.error(message)

    # Emit log to frontend
    socketio.emit("server_log", {"level": level.upper(), "message": message})


def emit_from_worker(event: str, data: dict, room: str):
    """
    A worker-safe function to emit a WebSocket event from a background process.
    It publishes the event to the Redis message queue, which the main server then forwards.
    """
    try:
        # This creates a temporary, lightweight publisher. It does not manage connections.
        worker_socketio = SocketIO(message_queue=redis_manager.get_redis_url())
        worker_socketio.emit(event, data, room=room)
        logger.info(f"📢 Worker dispatched event '{event}' to room '{room}' via Redis.")
    except Exception as e:
        logger.error(f"❌ Worker failed to dispatch event '{event}' to room '{room}': {e}")