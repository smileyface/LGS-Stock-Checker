from flask_socketio import SocketIO

import managers.redis_manager as redis_manager
from utility.logger import logger

# Initialize Flask-SocketIO
socketio = SocketIO(
    message_queue=redis_manager.get_redis_url(),
    cors_allowed_origins="*",
    async_mode="eventlet",
    engineio_logger=False
)

def initialize_socket_handlers():
    """
    Imports the socket handler modules.
    This is all that's needed to register the handlers with the main `socketio`
    instance, because they use the `@socketio.on()` decorator.
    """
    # By importing these modules, the @socketio.on decorators within them
    # are executed, registering the event handlers automatically.
    from . import socket_connections, socket_handlers, socket_events
    logger.info("✅ Socket.IO event handlers registered.")
