"""
This module centralizes all Socket.IO emission logic, providing helper
functions for sending messages from both the main Flask app and from
background RQ workers.
"""

from flask_socketio import SocketIO

from utility import logger
from .socket_manager import socketio
from .packing import pack_card
from managers.redis_manager import REDIS_URL
from managers import user_manager
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
        logger.error(
            f"❌ Worker failed to dispatch event '{event}' {target}: {e}")


def emit_message(message: messages.APIMessageResponses,
                 room: str = "") -> None:
    target = f"to room '{room}'" if room else "as a broadcast"
    logger.info(f"📢 Server emitting message '{message.name}' {target}.")
    socketio.emit(message.name, message.model_dump(), to=room)
    logger.info(f"📢 Server dispatched message '{message.name}' {target}.")


def send_user_cards(username: str):
    """Fetches a user's card list, formats it, and emits it over Socket.IO."""
    if not username:
        logger.error("❌ Attempted to send card list for an empty username.")
        return

    logger.info(f"📜 Fetching and sending tracked cards for user: {username}")
    cards = user_manager.load_card_list(username)

    # Format the cards to match the structure expected by the frontend.
    # This flattens the nested 'card' object into 'card_name'.
    packed_cards = []
    for card in cards:
        packed_cards.append(pack_card(card))

    # Emit a single event with the entire list to the user's room.
    payload = messages.CardListPayload.model_validate({"cards": packed_cards})
    message = messages.CardsDataMessage(payload=payload)
    emit_message(message, room=username)

    logger.info(
        f"📡 Sent card list to room '{username}' with {len(cards)} items.")
