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

    # 1. Initialize the Flask app using the dedicated manager
    app = flask_manager.initalize_flask_app(override_config, config_name)

    # 2. Configure Logging
    if app.debug and os.environ.get("LOG_LEVEL") != "DEBUG":
        os.environ["LOG_LEVEL"] = "DEBUG"
    set_log_level(logger)
    logger.info(f"Log level set to {os.environ.get('LOG_LEVEL')}")

    # 4. Initialize Core Managers
    flask_manager.login_manager_init(app)
    task_manager.init_task_manager()

    logger.info("✅ Base Flask app created and configured.")
    return app


def configure_database(app):
    """
    Configures the database for the Flask app.

    This includes:
    - Initializing the database connection with the app context
    - Setting up any necessary teardown handlers

    Args:
        app (Flask): The base Flask application instance.

    Returns:
        None
    """
    from data import database

    database.initialize_database(app.config.get("DATABASE_URL"))

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        database.remove_session()

    logger.info("✅ Database configured.")
    return app


def configure_socket_io(app):
    """
    Configures Socket.IO for real-time communication in the Flask app.

    This includes:
    - Initializing Socket.IO with the Flask app
    - Setting up any necessary event handlers

    Args:
        app (Flask): The base Flask application instance.

    Returns:
        None
    """
    from managers import socket_manager

    socket_manager.configure_socket_io(app)
    logger.info("✅ Socket.IO configured.")


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


def configure_scheduler_app(app):
    """
    Layers scheduler-specific configurations on top of a base Flask app.

    This includes:
    - Setting up the task scheduler
    - Registering any scheduler-specific blueprints or routes

    Args:
        app (Flask): The base Flask application instance.

    Returns:
        Flask: The fully configured scheduler application.
    """
    from managers import task_manager

    # 1. Initialize the scheduler
    task_manager.init_task_manager()

    logger.info("✅ Scheduler-specific configurations applied.")
    return app
