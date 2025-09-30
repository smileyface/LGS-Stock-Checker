import os
import logging
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
from flask_session import Session
import redis

login_manager = LoginManager()

def create_app(config_name=None, override_config=None):
    app = Flask(__name__)

    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'default')
    
    # --- Move imports inside the factory to prevent side effects ---
    from settings import config
    from routes import register_blueprints
    from managers.socket_manager import socketio, register_socket_handlers
    from managers.user_manager import load_user_by_id
    from managers.redis_manager.redis_manager import REDIS_URL
    from data.database.db_config import SessionLocal, initialize_database, startup_database

    # Import task modules to ensure they register themselves on startup.
    import tasks.card_availability_tasks
    import tasks.catalog_tasks

    # Apply ProxyFix middleware to make the app aware of proxy headers.
    # This is crucial for correct URL generation and security features when
    # running behind a reverse proxy like Nginx in Docker.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    app.config.from_object(config[config_name])
    if override_config:
        app.config.update(override_config)

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
    

    # Configure and initialize session management with Redis
    app.config['SESSION_TYPE'] = 'redis'
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_REDIS'] = redis.from_url(REDIS_URL)
    Session(app)

    # --- Initialize Flask-Login ---
    login_manager.init_app(app)
    login_manager.user_loader(load_user_by_id)

    # Register blueprints
    register_blueprints(app)

    # --- Configure CORS and SocketIO ---
    cors_origins_str = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:8000')

    allowed_origins = [origin.strip() for origin in cors_origins_str.split(',')]
    lgs_logger.info(f"🔌 CORS allowed origins configured: {allowed_origins}")

    message_queue_url = app.config.get("SOCKETIO_MESSAGE_QUEUE", REDIS_URL)

    # Initialize SocketIO with the app and specific configurations
    socketio.init_app(
        app,
        message_queue=message_queue_url,
        cors_allowed_origins=allowed_origins,
        async_mode="eventlet",
        engineio_logger=False  # Set to True for detailed Engine.IO debugging
    )
    # Discover and register all socket event handlers
    register_socket_handlers()
    
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

    @app.route('/api/health')
    def health_check():
        """
        Simple health check endpoint that returns a 200 OK response.
        Used by Docker's healthcheck to verify the application is running.
        """
        # In a more complex app, you might check DB/Redis connections here.
        return "OK", 200

    return app

# This block is only for running the local development server directly
if __name__ == "__main__":
    # Monkey patch for the development server when run directly.
    # This must be done before other imports that might initialize sockets.
    import eventlet
    eventlet.monkey_patch()

    app = create_app('development')
    # The host and port are passed here for the dev server run
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)
