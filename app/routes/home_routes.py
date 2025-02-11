from flask_socketio import SocketIO, emit
from flask import session

socketio = SocketIO()

@socketio.on('connect')
def handle_connect():
    print(f'User connected: {session.get("username", "Guest")}')

@socketio.on('get_home_page')
def handle_get_home_page():
    emit('home_page', {'message': 'Welcome to the LGS Stock Checker!'})
