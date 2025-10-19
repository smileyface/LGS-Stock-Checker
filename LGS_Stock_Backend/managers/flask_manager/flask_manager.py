from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
import os

from flask_login import LoginManager
from flask import session
from flask_session import Session

from managers import user_manager

from utility import logger

import routes

def initalize_flask_app(override_config=None, config_name=None):
    logger.info("🚀 Initializing Flask app...")
    app = Flask(__name__)

    if config_name is None:
        config_name = os.getenv("FLASK_CONFIG", "default")

    # Apply ProxyFix middleware to make the app aware of proxy headers.
    # This is crucial for correct URL generation and security features when
    # running behind a reverse proxy like Nginx in Docker.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # --- Configuration Loading ---
    from settings import config
    app.config.from_object(config[config_name])
    if override_config:
        app.config.update(override_config)

    config[config_name].init_app(app)

    # Initialize session management. The configuration (e.g., SESSION_TYPE)
    # is now correctly loaded from the config object.
    Session(app)
    logger.info("✅ Flask app configured successfully")

    return app

def login_manager_init(app):
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.user_loader(user_manager.load_user_by_id)

def register_blueprints(app):
    routes.register_blueprints(app)

def health_check():
    if not session:
        logger.error("❌ Health check failed: No session found")
        return False
    return True