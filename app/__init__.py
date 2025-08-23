import os

import redis
from flask import Flask
from flask_session import Session

from app.routes import register_blueprints
from managers.socket_manager import socketio


def create_app(config_override=None):
    app = Flask(__name__)

    # Use environment variable for security
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "your-secret-key")

    # 🔧 Configure Redis-based session storage
    app.config["SESSION_TYPE"] = "redis"
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_USE_SIGNER"] = True
    app.config["SESSION_KEY_PREFIX"] = "session:"
    app.config["SESSION_REDIS"] = redis.Redis(host="redis", port=6379)

    # Apply overrides for testing or other environments
    if config_override:
        app.config.update(config_override)

    # Initialize session management
    Session(app)

    # Register blueprints
    register_blueprints(app)

    # Attach SocketIO with Redis message queue
    socketio.init_app(app, message_queue="redis://redis:6379")

    return app
