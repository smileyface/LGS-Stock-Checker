import logging
import os
import eventlet
from flask import Flask, jsonify
from flask_socketio import SocketIO, join_room
from flask_login import LoginManager
from settings import LOGGING_LEVEL, LOGGER_NAME
from managers.redis_manager.redis_manager import REDIS_URL
from routes import auth_routes, user_routes
from managers.socket_manager import register_socket_handlers, socketio
from managers.user_manager import load_user_by_id

# --- Setup ---
logger = logging.getLogger(LOGGER_NAME)
app = Flask(__name__)
login_manager = LoginManager()
# --- Initialize Flask-Login ---
login_manager.init_app(app)
login_manager.user_loader(load_user_by_id)

# --- Configuration (Add CORS Configuration Here) ---
# Environment variables for CORS setup
FRONTEND_URL = os.environ.get('FRONTEND_URL', '*')

# NOTE: The default setting in Flask-SocketIO is restrictive. 
# Explicitly setting CORS to allow the frontend connection is necessary 
# to fix the HTTP 400 Bad Request errors seen in the logs.
socketio = SocketIO(
    app, 
    async_mode='eventlet', 
    message_queue=REDIS_URL,
    cors_allowed_origins=FRONTEND_URL, # Allow connections from the frontend
    engineio_logger=True # Enable EngineIO internal logging
)

# --- Routes and Handlers ---
app.register_blueprint(auth_routes.auth_bp)
app.register_blueprint(user_routes.user_bp)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    logging.INFO("📢 Sent health check response.")
    return jsonify({"status": "ok"}), 200

# Register Socket.IO event handlers
register_socket_handlers()


# --- Main Run Block ---
if __name__ == '__main__':
    # Initialize logger
    logging.basicConfig(level=LOGGING_LEVEL)
    logger.info(f"🚀 Starting LGS Stock Checker Backend...")
    logger.info(f"Using Redis at {REDIS_URL}")
    logger.info(f"CORS allowed origins: {FRONTEND_URL}")

    try:
        # We need eventlet.wsgi.server to properly handle both Flask requests and SocketIO connections
        eventlet.wsgi.server(eventlet.listen(('', 5000)), app)
    except KeyboardInterrupt:
        logger.info("👋 Shutting down scheduler and server.")
        socketio.stop()
        eventlet.wsgi.server.stop()
