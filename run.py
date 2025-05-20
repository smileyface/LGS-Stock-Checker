from managers.tasks_manager import register_redis_function
from utility.logger import logger

import eventlet

eventlet.monkey_patch()

from app import create_app
from managers.socket_manager.socket_manager import socketio, register_socket_events  # Import the initialized SocketIO

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        logger.info("🔹 Starting Flask-SocketIO server...")
        register_socket_events(socketio)
        register_redis_function()
        socketio.run(app, debug=True, host="0.0.0.0", port=5000)
