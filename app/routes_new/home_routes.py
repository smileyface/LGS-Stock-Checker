from flask_socketio import SocketIO, emit
from flask import session, Blueprint, render_template

socketio = SocketIO()

home_bp = Blueprint("home_bp", __name__)
@home_bp.route("/")
def index():
    return render_template("index.html")

@socketio.on('connect')
def handle_connect():
    print(f'User connected: {session.get("username", "Guest")}')

@socketio.on('get_home_page')
def handle_get_home_page():
    emit('home_page', {'message': 'Welcome to the LGS Stock Checker!'})
