import os
import logging

def create_app(config_name=None, override_config=None, database_url=None, skip_scheduler=False):

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
    from managers import task_manager
    from data import database
    from utility import logger

    task_manager.init_task_manager()

    socket_manager.configure_socket_io(app)


    # Use the provided database_url, or fall back to the environment variable.
    # This allows tests to inject a different database URL.
    db_url = database_url or os.environ.get("DATABASE_URL")

    if db_url:
        database.initialize_database(db_url)
        # The startup_database function syncs stores, which requires tables to exist.
        # In a test environment, tables are created by fixtures, so we skip this.
        if config_name != "testing":
            database.startup_database()

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        database.remove_session()

    logger.info("✅ Flask app created successfully")
    return app

# This block is only for running the local development server directly via `python run.py`.
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
