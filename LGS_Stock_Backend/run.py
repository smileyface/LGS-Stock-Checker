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

    





    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        database.initialize_database(database_url)
        database.startup_database()

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        database.remove_session()

    return app
