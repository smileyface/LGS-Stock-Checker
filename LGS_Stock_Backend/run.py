import os
import redis
import eventlet

# Crucial for SocketIO performance with Gunicorn and event-based workers
eventlet.monkey_patch()

from flask import Flask
from flask_session import Session

# Use absolute imports for clarity and robustness, as supported by your PYTHONPATH
from LGS_Stock_Backend.routes import register_blueprints
from LGS_Stock_Backend.managers.socket_manager import socketio, initialize_socket_handlers


def create_app(config_override=None):
    app = Flask(__name__)

    # Use environment variable for security
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "a-very-secret-key")

    # 🔧 Configure Redis-based session storage
    app.config["SESSION_TYPE"] = "redis"
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_USE_SIGNER"] = True
    app.config["SESSION_KEY_PREFIX"] = "session:"
    redis_host = os.getenv("REDIS_HOST", "redis")
    app.config["SESSION_REDIS"] = redis.Redis(host=redis_host, port=6379)

    # Apply overrides for testing or other environments
    if config_override:
        app.config.update(config_override)

    # Initialize session management
    Session(app)

    # Register blueprints
    register_blueprints(app)

    # Initialize SocketIO with the app and specific configurations
    socketio.init_app(
        app,
        message_queue=f"redis://{redis_host}:6379",
        cors_allowed_origins="*",
        async_mode="eventlet",
        engineio_logger=False  # Set to True for detailed Engine.IO debugging
    )
    # Discover and register all socket event handlers
    initialize_socket_handlers()

    return app

# This block is only for running the local development server directly
if __name__ == "__main__":
    app = create_app()
    # The host and port are passed here for the dev server run
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)
