import os
from utility import logger, set_log_level


def create_base_app(config_name=None, override_config=None, database_url=None):
    """
    Creates and configures the core Flask application instance.

    This factory handles essential setup common to all processes (web, worker,
    scheduler), including:
    - Flask app initialization (via flask_manager)
    - Configuration loading
    - Logging setup
    - Database connection initialization
    - Login manager setup
    - Task manager initialization

    Args:
        config_name (str, optional): The configuration profile to use
                                     (e.g., 'development', 'testing').
        override_config (dict, optional): A dictionary of config values to
                                          override.
        database_url (str, optional): A specific database URL to use,
                                      overriding environment variables.

    Returns:
        Flask: The configured base Flask application instance.
    """
    from managers import flask_manager
    from managers import task_manager
    from data import database

    # 1. Initialize the Flask app using the dedicated manager
    app = flask_manager.initalize_flask_app(override_config, config_name)

    # 2. Configure Logging
    if app.debug and os.environ.get("LOG_LEVEL") != "DEBUG":
        os.environ["LOG_LEVEL"] = "DEBUG"
    set_log_level(logger)
    logger.info(f"Log level set to {os.environ.get('LOG_LEVEL')}")
    
    # 3. Initialize Database
    db_url = database_url or os.environ.get("DATABASE_URL")
    if db_url:
        database.initialize_database(db_url)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        database.remove_session()
        
    # 4. Initialize Core Managers
    flask_manager.login_manager_init(app)
    task_manager.init_task_manager()

    logger.info("✅ Base Flask app created and configured.")
    return app


def configure_web_app(app):
    """
    Layers web-specific configurations on top of a base Flask app.

    This includes:
    - Registering API blueprints (routes)
    - Configuring Socket.IO for real-time communication
    - Starting the background listener for worker results

    Args:
        app (Flask): The base Flask application instance.

    Returns:
        Flask: The fully configured web application.
    """
    from managers import socket_manager
    from managers import flask_manager

    # 1. Register API routes
    flask_manager.register_blueprints(app)

    # 2. Configure Socket.IO
    socket_manager.configure_socket_io(app)

    # 3. Start the background listener for results from RQ workers
    flask_manager.start_server_listener(app)

    logger.info("✅ Web-specific configurations applied.")
    return app


def create_worker_app():
    """
    Creates a minimal Flask app context for the RQ worker.

    This allows tasks to access the database and other extensions.

    Returns:
        Flask: A basic, configured Flask application instance.
    """
    # For the worker, we only need the base app to establish context.
    return create_base_app()