from flask import request
from flask_socketio import join_room
from flask_login import current_user
from .socket_manager import socketio
from utility import logger


@socketio.on("connect")
def handle_connect():
    """
    Handle new WebSocket connections.
    If the user is authenticated via the session, they are joined to a
    user-specific room.
    """
    # Flask-Login's `current_user` proxy correctly loads the user from the
    # shared Redis session, even when the request is handled by a
    # different worker.
    if current_user.is_authenticated:
        username = current_user.username
        join_room(username)
        # Use `request.sid` as the canonical way to get the session ID for the
        # current event.
        logger.info(
            f"🟢 Client connected: {request.sid}, "
            f"User: {username}, "
            f"Room: {username}"
        )
    else:
        # Handle anonymous or unauthenticated connections if necessary.
        logger.info(f"🟢 Anonymous client connected: {request.sid}")


@socketio.on("disconnect")
def handle_disconnect():
    """Handle WebSocket disconnections."""
    # Flask-SocketIO automatically handles leaving rooms on disconnect.
    logger.info(f"🔴 Client disconnected: {request.sid}")
