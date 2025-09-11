import os
import eventlet

# Crucial for SocketIO performance with Gunicorn and event-based workers
eventlet.monkey_patch()

from flask import Flask
from flask_session import Session

# Use imports relative to the LGS_Stock_Backend package root
from settings import config
from routes import register_blueprints
from managers.socket_manager import socketio, initialize_socket_handlers
from managers.tasks_manager import register_redis_function


def create_app(config_name=None):
    app = Flask(__name__)

    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'default')
    
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # Initialize session management
    Session(app)

    # Register blueprints
    register_blueprints(app)

    redis_host = os.getenv("REDIS_HOST", "redis")
    # When running behind a reverse proxy, we must specify the allowed origins
    # for CORS to allow credentials (session cookies) to be sent.
    # The "*" wildcard is not allowed by browsers when credentials are used.
    allowed_origins_str = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:8000")
    allowed_origins = [origin.strip() for origin in allowed_origins_str.split(',')]

    # Initialize SocketIO with the app and specific configurations
    socketio.init_app(
        app,
        message_queue=f"redis://{redis_host}:6379",
        cors_allowed_origins=allowed_origins,
        async_mode="eventlet",
        engineio_logger=False  # Set to True for detailed Engine.IO debugging
    )
    # Discover and register all socket event handlers
    initialize_socket_handlers()

    # Discover and register all background tasks for the RQ worker
    register_redis_function()

    return app

# This object is what Gunicorn will look for.
# It's created by calling the factory function.
app = create_app()

# This block is only for running the local development server directly
if __name__ == "__main__":
    app = create_app('development')
    # The host and port are passed here for the dev server run
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)
