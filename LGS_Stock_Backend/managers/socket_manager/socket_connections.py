from flask import request
from flask_socketio import join_room
from flask_login import current_user
from .socket_manager import socketio
from utility import logger


@socketio.on('connect')
def handle_connect():
    """Handle new WebSocket connections and assign them to a user-specific room."""
    # Flask-Login's current_user is automatically available in the SocketIO context
    if current_user.is_authenticated:
        username = current_user.username
        # Add the client to a room named after their username for targeted messaging.
        join_room(username)
        logger.info(f"🟢 Client connected: {request.sid}, User: {username}, Room: {username}")
    else:
        # Handle anonymous or unauthenticated connections if necessary.
        logger.info(f"🟢 Anonymous client connected: {request.sid}")


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnections."""
    # Flask-SocketIO automatically handles leaving rooms on disconnect.
    logger.info(f"🔴 Client disconnected: {request.sid}")
