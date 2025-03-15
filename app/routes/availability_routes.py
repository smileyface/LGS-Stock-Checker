from flask_socketio import SocketIO, emit
from flask import session, Blueprint

socketio = SocketIO()

availability_bp = Blueprint("availability_bp", __name__)


@socketio.on('connect')
def handle_connect():
    print(f'User connected: {session.get("username", "Guest")}')