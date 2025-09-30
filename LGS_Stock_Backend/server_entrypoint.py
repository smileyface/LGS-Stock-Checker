"""
Application entrypoint for running with Gunicorn in a container.
This file creates and configures the Flask app and its extensions.
"""
import logging
import os
from flask import Flask, jsonify
from flask_login import LoginManager
from flask_session import Session
from werkzeug.middleware.proxy_fix import ProxyFix

from data.database.db_config import (SessionLocal, initialize_database,
                                     startup_database)
from managers.redis_manager.redis_manager import REDIS_URL
from managers.socket_manager import register_socket_handlers, socketio
from managers.user_manager import load_user_by_id
from routes import register_blueprints
from settings import config
from utility import logger

# Import task modules to ensure they register themselves on startup.
import tasks.card_availability_tasks
import tasks.catalog_tasks

# --- App Creation and Configuration ---
app = Flask(__name__)

# Apply ProxyFix middleware for running behind a reverse proxy like Nginx.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Load configuration from settings.py based on FLASK_CONFIG env var.
config_name = os.getenv('FLASK_CONFIG', 'default')
app.config.from_object(config[config_name])
config[config_name].init_app(app)

# --- Logging Configuration ---
log_level_name = os.environ.get('LOG_LEVEL', 'INFO').upper()
if app.debug:
    log_level_name = 'DEBUG'
logger.setLevel(log_level_name)
logger.info(f"📝 Logger for 'LGS_Stock_Checker' set to level: {log_level_name}")

# --- Initialize Extensions ---
Session(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.user_loader(load_user_by_id)

# --- Register Blueprints ---
register_blueprints(app)

# --- Configure CORS and SocketIO ---
cors_origins_str = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:8000')
allowed_origins = [origin.strip() for origin in cors_origins_str.split(',')]
logger.info(f"🔌 CORS allowed origins configured: {allowed_origins}")

socketio.init_app(app, message_queue=REDIS_URL, cors_allowed_origins=allowed_origins, async_mode="eventlet")
register_socket_handlers()

# --- Database Initialization ---
database_url = os.environ.get("DATABASE_URL")
if database_url:
    initialize_database(database_url)
    startup_database()
else:
    logger.error("💥 DATABASE_URL not found. Server cannot run.")
    exit(1)

@app.teardown_appcontext
def shutdown_session(exception=None):
    """Remove the database session after each request to prevent leaks."""
    if SessionLocal:
        SessionLocal.remove()

@app.route('/api/health')
def health_check():
    """Simple health check endpoint for Docker."""
    return "OK", 200
