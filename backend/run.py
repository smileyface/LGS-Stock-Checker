import os
from utility.logger import logger, set_log_level


def create_app(config_name=None,
               override_config=None,
               database_url=None,
               skip_scheduler=False):

    from managers import flask_manager

    app = flask_manager.initalize_flask_app(override_config, config_name)
    flask_manager.login_manager_init(app)
    flask_manager.register_blueprints(app)

    if app.debug and os.environ.get("LOG_LEVEL") != "DEBUG":
        os.environ["LOG_LEVEL"] = "DEBUG"

    set_log_level(logger)

    logger.info(f"CREATE_APP: LOG_LEVEL is {os.environ.get('LOG_LEVEL')}")

    set_log_level(logger)

    # Logger Configuration (MUST happen after config, before other imports)

    logger.info(f"CREATE_APP: LOG_LEVEL is {os.environ.get('LOG_LEVEL')}")

    # Move imports inside the factory to prevent side effects
    from managers import socket_manager
    from managers import flask_manager
    from managers import task_manager
    from data import database

    task_manager.init_task_manager()

    socket_manager.configure_socket_io(app)

    # Start the background thread to listen for worker results
    flask_manager.start_server_listener(app)

    # Use the provided database_url, or fall back to the environment variable.
    # This allows tests to inject a different database URL.
    db_url = database_url or os.environ.get("DATABASE_URL")

    if db_url:
        database.initialize_database(db_url)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        database.remove_session()

    logger.info("✅ Flask app created successfully")
    print("--- CREATE_APP: FINISHED ---")
    return app


# This block is only for running the local development server
# directly via `python run.py`.
# It is the entrypoint used by `docker-compose.dev.yml`.
if __name__ == "__main__":
    # Monkey patch for the development server when run directly.
    # This must be done before other imports that might initialize sockets.
    import eventlet

    eventlet.monkey_patch()

    from managers import socket_manager

    app = create_app("development")
    # The host and port are passed here for the dev server run.
    socket_manager.socketio.run(app, debug=True, host="0.0.0.0", port=5000)
