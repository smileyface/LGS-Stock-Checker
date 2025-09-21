import os
import eventlet
import logging

# Crucial for SocketIO performance with Gunicorn and event-based workers
eventlet.monkey_patch()

from flask import Flask
from flask_session import Session

# Use imports relative to the LGS_Stock_Backend package root
from settings import config
from routes import register_blueprints
from managers.socket_manager import socketio, initialize_socket_handlers
from managers.tasks_manager import register_redis_function
from data.database.db_config import SessionLocal, initialize_database, startup_database


def create_app(config_name=None):
    app = Flask(__name__)

    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'default')
    
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # --- Configure application-wide logging ---
    # Set the log level from an environment variable, defaulting to INFO.
    # If the app is in debug mode (via FLASK_CONFIG=development), force DEBUG level.
    log_level_name = os.environ.get('LOG_LEVEL', 'INFO').upper()
    if app.debug:
        log_level_name = 'DEBUG'
    
    # Based on your log files, the custom logger is named 'LGS_Stock_Checker'.
    # We get this specific logger and set its level. The handlers are assumed
    # to be configured in the `utility.logger` module.
    lgs_logger = logging.getLogger('LGS_Stock_Checker')
    lgs_logger.setLevel(log_level_name)
    lgs_logger.info(f"📝 Logger for 'LGS_Stock_Checker' set to level: {log_level_name}")
    

    # Initialize session management
    Session(app)

    # Register blueprints
    register_blueprints(app)

    # --- Configure CORS and SocketIO ---
    redis_host = os.getenv("REDIS_HOST", "redis")

    # Read allowed origins from the environment variable. This allows flexible
    # configuration for different environments (dev, prod) without code changes.
    # The variable should be a comma-separated string.
    cors_origins_str = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:8000')
    allowed_origins = [origin.strip() for origin in cors_origins_str.split(',')]
    lgs_logger.info(f"🔌 CORS allowed origins configured: {allowed_origins}")

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
    
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        initialize_database(database_url)
        startup_database()
        
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        """Remove the database session after each request to prevent leaks."""
        # This check prevents an error if the app is run without a DATABASE_URL,
        # in which case SessionLocal would be None.
        if SessionLocal:
            SessionLocal.remove()

    return app

# This block is only for running the local development server directly
if __name__ == "__main__":
    app = create_app('development')
    # The host and port are passed here for the dev server run
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)
