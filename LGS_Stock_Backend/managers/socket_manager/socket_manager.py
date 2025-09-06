from flask_socketio import SocketIO

from utility.logger import logger

# Create a single, uninitialized SocketIO instance.
# It will be configured and initialized in the application factory.
socketio = SocketIO()

def initialize_socket_handlers():
    """
    Imports the socket handler modules.
    This is all that's needed to register the handlers with the main `socketio`
    instance, because they use the `@socketio.on()` decorator.
    """
    # By importing these modules, the @socketio.on decorators within them
    # are executed, registering the event handlers automatically.
    from . import socket_connections, socket_handlers
    logger.info("✅ Socket.IO event handlers registered.")
