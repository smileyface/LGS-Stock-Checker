import os
import logging
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
from flask_session import Session
import redis

login_manager = LoginManager()


def create_app(config_name=None, override_config=None, skip_scheduler=False):
    app = Flask(__name__)

    if config_name is None:
        config_name = os.getenv("FLASK_CONFIG", "default")

    # --- Configuration Loading ---
    from settings import config
    app.config.from_object(config[config_name])
    if override_config:
        app.config.update(override_config)

    # --- Logger Configuration (MUST happen after config, before other imports) ---
    if app.debug and os.environ.get("LOG_LEVEL") != "DEBUG":
        os.environ["LOG_LEVEL"] = "DEBUG"

    # --- Move imports inside the factory to prevent side effects ---
    from settings import config
    from routes import register_blueprints
    from managers import user_manager
    from managers import socket_manager
    from managers import redis_manager
    from data import database
    from utility import logger


    # Import task modules to ensure they register themselves on startup.
    import tasks.card_availability_tasks
    import tasks.catalog_tasks

    # Apply ProxyFix middleware to make the app aware of proxy headers.
    # This is crucial for correct URL generation and security features when
    # running behind a reverse proxy like Nginx in Docker.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    config[config_name].init_app(app)


    # Initialize session management. The configuration (e.g., SESSION_TYPE)
    # is now correctly loaded from the config object.
    Session(app)

    # --- Initialize Flask-Login ---
    login_manager.init_app(app)
    login_manager.user_loader(user_manager.load_user_by_id)

    # Register blueprints
    register_blueprints(app)

    # --- Configure CORS and SocketIO ---
    cors_origins_str = os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:8000")

    allowed_origins = [origin.strip() for origin in cors_origins_str.split(",")]
    logger.info(f"🔌 CORS allowed origins configured: {allowed_origins}")

    message_queue_url = app.config.get(
        "SOCKETIO_MESSAGE_QUEUE", redis_manager.REDIS_URL
    )

    # Initialize SocketIO with the app and specific configurations
    socket_manager.socketio.init_app(
        app,
        message_queue=message_queue_url,
        cors_allowed_origins=allowed_origins,
        async_mode="eventlet",
        engineio_logger=False,  # Set to True for detailed Engine.IO debugging
    )
    # Discover and register all socket event handlers
    socket_manager.register_socket_handlers()

    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        database.initialize_database(database_url)
        database.startup_database()

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        database.remove_session()


# This block is only for running the local development server directly
if __name__ == "__main__":
    # Monkey patch for the development server when run directly.
    # This must be done before other imports that might initialize sockets.
    import eventlet

    eventlet.monkey_patch()
    
    from managers import socket_manager

    app = create_app("development")
    # The host and port are passed here for the dev server run
    socket_manager.socketio.run(app, debug=True, host="0.0.0.0", port=5000)
    # This must be done before other imports that might initialize sockets.
    import eventlet

    eventlet.monkey_patch()
    
    from managers import socket_manager

    app = create_app("development")
    # The host and port are passed here for the dev server run
    socket_manager.socketio.run(app, debug=True, host="0.0.0.0", port=5000)
