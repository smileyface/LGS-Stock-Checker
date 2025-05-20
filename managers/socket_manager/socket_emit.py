from managers.socket_manager import socketio
from utility.logger import logger


def emit_card_availability_data(username, store_name, card_name, items):
    # Emit WebSocket event to update UI
    logger.info(f"📡 Preparing WebSocket event for {card_name} at {store_name} (User: {username})")
    socketio.emit(
        "card_availability_data",
        {
            "username": username,
            "store": store_name,
            "card": card_name,
            "items": items
        },
        namespace="/"
    )