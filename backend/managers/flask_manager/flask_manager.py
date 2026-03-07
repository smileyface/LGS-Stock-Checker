from werkzeug.middleware.proxy_fix import ProxyFix
from pydantic import ValidationError # noqa
import os
from flask import Flask, jsonify  # noqa
from flask_login import LoginManager  # noqa
from flask import session  # noqa
from flask_session import Session  # noqa

from managers import user_manager  # noqa
from utility import logger  # noqa
import routes  # noqa


def initalize_flask_app(override_config=None, config_name=None):
    logger.info("🚀 Initializing Flask app...")
    app = Flask(__name__)

    if config_name is None:
        config_name = os.getenv("FLASK_CONFIG", "default")

    # Apply ProxyFix middleware to make the app aware of proxy headers.
    # This is crucial for correct URL generation and security features when
    # running behind a reverse proxy like Nginx in Docker.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1,
                            x_proto=1, x_host=1, x_prefix=1)

    # --- Configuration Loading ---
    from settings import config

    app.config.from_object(config[config_name])
    if override_config:
        app.config.update(override_config)

    config[config_name].init_app(app)

    # --- Global Error Handlers ---
    @app.errorhandler(ValidationError)
    def handle_pydantic_validation_error(e):
        """
        Catches any Pydantic ValidationError raised in any route 
        and returns a 400 instead of a 500.
        """
        logger.warning(f"⚠️ Validation Error: {e.json()}")
        return jsonify({
            "error": "Invalid request data",
            "details": e.errors()
        }), 400

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
    """
    Performs a health check on the Flask session mechanism.

    It verifies that the session is operational by writing and reading a test
    value.
    This implicitly checks the connection to the session backend (e.g., Redis).
    """
    try:
        # A simple key to test the session functionality.
        session["health_check"] = "ok"
        if session.get("health_check") == "ok":
            return True
        return False
    except Exception as e:
        logger.error(f"❌ Flask Session health check failed: {e}")
        return False
