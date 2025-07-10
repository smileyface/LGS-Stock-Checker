import eventlet

eventlet.monkey_patch()

from managers import availability_manager
from managers.tasks_manager import register_redis_function
from managers.set_manager import initialize_set_data
from utility.logger import logger

from app import create_app
from managers.socket_manager import socketio, initialize_socket_handlers

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        logger.info("🔹 Starting Flask-SocketIO server...")
        initialize_socket_handlers()
        register_redis_function()
        initialize_set_data()

        # Schedule recurring background tasks
        availability_manager.queue_wanted_card_updates()

        socketio.run(app, debug=True, host="0.0.0.0", port=5000)
