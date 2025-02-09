import eventlet
eventlet.monkey_patch()

from app import create_app
from managers.socket_manager.socket_manager import socketio  # Import the initialized SocketIO

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        socketio.run(app, debug=True, host="0.0.0.0", port=5000)
