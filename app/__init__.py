import json
import os

import requests
from flask import Flask
import redis
from flask_session import Session
from app.routes import register_blueprints
from managers.socket_manager import socketio

from app.caching import get_cached_card_names, initialize_cache


def create_app():
    app = Flask(__name__)

    # ✅ Use environment variable for security
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "your-secret-key")

    # 🔧 Configure Redis-based session storage
    app.config["SESSION_TYPE"] = "redis"
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_USE_SIGNER"] = True
    app.config["SESSION_KEY_PREFIX"] = "session:"
    app.config["SESSION_REDIS"] = redis.Redis(host="redis", port=6379)
    # ✅ Initialize session management
    Session(app)

    # ✅ Register blueprints
    register_blueprints(app)

    # ✅ Attach SocketIO with Redis message queue
    socketio.init_app(app, message_queue="redis://redis:6379")

    # ✅ Initialize card name cache
    initialize_cache(app.config["SESSION_REDIS"])

    return app
