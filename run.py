from utility.logger import logger

import eventlet
eventlet.monkey_patch()

from app import create_app
from managers.socket_manager.socket_manager import init_socketio  # Import the initialized SocketIO
from managers.extensions import socketio

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        logger.info("🔹 Starting Flask-SocketIO server...")
        init_socketio(app)
        socketio.run(app, debug=True, host="0.0.0.0", port=5000)
