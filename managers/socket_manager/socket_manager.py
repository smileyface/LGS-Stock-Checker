from typing import Literal
from flask_socketio import SocketIO

from managers.redis_manager.redis_manager import REDIS_URL
from utility.logger import logger

# Initialize Flask-SocketIO
socketio = SocketIO(
    message_queue=REDIS_URL,
    cors_allowed_origins="*",
    async_mode="eventlet",
    engineio_logger=False
)

# Store active WebSocket connections
connected_clients = set()

# 🔹 WebSocket Connection Handling
from managers.socket_manager.socket_connections import handle_connect

# 🔹 WebSocket Event Handling
from managers.socket_manager.socket_handlers import handle_get_cards, handle_get_card_availability, \
    handle_update_user_tracked_cards, \
    handle_parse_card_list, handle_request_card_names, handle_add_user_tracked_card, handle_delete_user_tracked_card


def log_and_emit(level: Literal['info', 'warning', 'error'], message: str) -> None:
    """
    Logs a message to the backend logger and emits it to the frontend.

    Args:
        level (str): The severity level of the log message ('info', 'warning', 'error').
        message (str): The log message to be recorded and emitted.
    """
    log_methods = {
        "info": logger.info,
        "warning": logger.warning,
        "error": logger.error
    }
    
    log_method = log_methods.get(level)
    if log_method:
        log_method(message)
    else:
        raise ValueError(f"Invalid log level: {level}")

    # Emit log to frontend
    socketio.emit("server_log", {"level": level.upper(), "message": message})


def register_socket_events(socket_io: SocketIO):
    """
    Registers all WebSocket event handlers with the provided SocketIO instance.

    This function binds specific event names to their corresponding handler
    functions, enabling the server to respond to WebSocket events such as
    client connections, card management requests, and card list parsing.

    Args:
        socket_io (SocketIO): The SocketIO instance to register the event handlers with.
    """
    events = {
        "connect": handle_connect,
        "get_cards": handle_get_cards,
        "get_card_availability": handle_get_card_availability,
        "parse_card_list": handle_parse_card_list,
        "request_card_names": handle_request_card_names,
        "add_card": handle_add_user_tracked_card,
        "delete_card": handle_delete_user_tracked_card,
        "update_card": handle_update_user_tracked_cards,
    }

    for event, handler in events.items():
        socket_io.on_event(event, handler)
