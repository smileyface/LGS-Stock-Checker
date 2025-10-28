import os

def create_app(config_name=None, override_config=None):

    from managers import flask_manager
    app = flask_manager.initalize_flask_app(override_config, config_name)
    flask_manager.login_manager_init(app)
    flask_manager.register_blueprints(app)

    # --- Logger Configuration (MUST happen after config, before other imports) ---
    if app.debug and os.environ.get("LOG_LEVEL") != "DEBUG":
        os.environ["LOG_LEVEL"] = "DEBUG"

    # --- Move imports inside the factory to prevent side effects ---
    from managers import socket_manager
    from managers import task_manager
    from tasks import scheduler_setup
    from utility import logger

    task_manager.init_task_manager()

    socket_manager.configure_socket_io(app)
    scheduler_setup.schedule_recurring_tasks()

    

    logger.info("✅ Flask app created successfully")
    return app

if __name__ == "__main__":
    # Monkey patch for the development server when run directly.
    # This must be done before other imports that might initialize sockets.
    import eventlet
    eventlet.monkey_patch()

    app = create_app("development")
    # The host and port are passed here for the dev server run.