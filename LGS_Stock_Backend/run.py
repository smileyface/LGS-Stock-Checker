import os
import logging

def create_app(config_name=None, override_config=None, skip_scheduler=False):

    from managers import flask_manager
    app = flask_manager.initalize_flask_app(override_config, config_name)
    flask_manager.login_manager_init(app)
    flask_manager.register_blueprints(app)

    # --- Logger Configuration (MUST happen after config, before other imports) ---
    if app.debug and os.environ.get("LOG_LEVEL") != "DEBUG":
        os.environ["LOG_LEVEL"] = "DEBUG"

    # --- Move imports inside the factory to prevent side effects ---
    from managers import socket_manager
    from managers import redis_manager
    from data import database
    from utility import logger


    # Import task modules to ensure they register themselves on startup.
    import tasks.card_availability_tasks
    import tasks.catalog_tasks

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

    return app
