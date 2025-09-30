from flask import request
from flask_socketio import join_room
from flask_login import current_user
from .socket_manager import socketio
from utility import logger


# LGS_Stock_Backend/managers/socket_manager/socket_connections.py

from flask import request, session
from flask_socketio import join_room
# 💡 FIX: Import necessary Flask-Login components
from flask_login import current_user, login_user, logout_user 
from managers.user_manager import load_user_by_id # <-- Already defined/imported in run.py
from .socket_manager import socketio
from utility import logger


@socketio.on('connect')
def handle_connect():
    """Handle new WebSocket connections and assign them to a user-specific room."""
    # 💡 FIX: Manually load the user from the session if Flask-Login hasn't done it 
    # (which it won't reliably do for polling requests outside of a full HTTP cycle).
    
    # Flask-Login stores the user ID in the 'user_id' session key (its default).
    user_id = session.get("_user_id") 

    if user_id:
        # Load the user object and set it in the request context for Flask-Login checks
        user = load_user_by_id(user_id) 
        
        if user and user.is_active:
            # We must explicitly call login_user to attach the user object to the current request context.
            # This is essential for transport upgrades (polling -> websocket).
            login_user(user, remember=True) 

            # Now we can proceed with the original logic using current_user or the session.
            username = user.username # Assuming you added username property to your FlaskLoginUser or fetch it here
            
            # Add the client to a room named after their username for targeted messaging.
            join_room(username)
            logger.info(f"🟢 Client connected: {session.get('socketio_sid')}, User: {username}, Room: {username}")
        else:
            logger.warning(f"🔒 Client connected: {session.get('socketio_sid')}, but user ID {user_id} is invalid or inactive. Rejecting.")
            # Explicitly clear session and reject
            session.clear()
            return False
            
    else:
        # Handle anonymous or unauthenticated connections if necessary.
        logger.info(f"🟢 Anonymous client connected: {session.get('socketio_sid')}")
        # If your dashboard requires login, you can reject here too:
        # return False

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnections."""
    # Flask-SocketIO automatically handles leaving rooms on disconnect.
    logger.info(f"🔴 Client disconnected: {session.get('socketio_sid')}")
