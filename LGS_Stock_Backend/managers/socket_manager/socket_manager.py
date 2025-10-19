import os
from flask_socketio import SocketIO

from managers import redis_manager

from utility import logger

# Create a single, uninitialized SocketIO instance.
# It will be configured and initialized in the application factory.
socketio = SocketIO()

def register_socket_handlers():
    """
    Imports the socket handler modules.
    This is all that's needed to register the handlers with the main `socketio`
    instance, because they use the `@socketio.on()` decorator.
    """
    # By importing these modules, the @socketio.on decorators within them
    # are executed, registering the event handlers automatically.
    from . import socket_connections, socket_handlers
    logger.info("✅ Socket.IO event handlers registered.")

def configure_socket_io(app):

        # --- Configure CORS and SocketIO ---
    cors_origins_str = os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:8000")

    allowed_origins = [origin.strip() for origin in cors_origins_str.split(",")]
    logger.info(f"🔌 CORS allowed origins configured: {allowed_origins}")

    message_queue_url = app.config.get(
        "SOCKETIO_MESSAGE_QUEUE", redis_manager.REDIS_URL
    )
        # Initialize SocketIO with the app and specific configurations
    socketio.init_app(
        app,
        message_queue=message_queue_url,
        cors_allowed_origins=allowed_origins,
        async_mode="eventlet",
        engineio_logger=False,  # Set to True for detailed Engine.IO debugging
    )
    # Discover and register all socket event handlers
    register_socket_handlers()

def health_check():
    """
    Performs a health check on the Socket.IO server instance.

    This check verifies that the Socket.IO server has been initialized and
    is configured with a Redis message queue, which is critical for a
    multi-process environment.
    """
    try:
        # 1. Check if the server has been initialized by init_app()
        if not hasattr(socketio, 'server') or not socketio.server:
            raise RuntimeError("Socket.IO server has not been initialized.")

        # 2. Check if the client manager is configured for Redis.
        # This is crucial for multi-process communication (e.g., with workers).
        # The class name check ensures we're not using the default in-memory manager.
        if 'RedisManager' not in socketio.server.manager.__class__.__name__:
            raise RuntimeError("Socket.IO is not configured with a Redis message queue.")

        return True
    except Exception as e:
        logger.error(f"❌ Socket.IO health check failed: {e}")
        return False