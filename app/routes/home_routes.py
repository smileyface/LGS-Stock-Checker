from flask_socketio import SocketIO, emit
from flask import session, Blueprint, render_template, redirect, url_for

socketio = SocketIO()

home_bp = Blueprint("home_bp", __name__)
@home_bp.route("/")
def landing_page():
    if "username" in session:
        return redirect(url_for("dashboard"))
    return render_template("landing.html")

@home_bp.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("landing_page"))
    return render_template("dashboard.html",
                           username=session["username"],
                           card_availability=get_card_availability())

@socketio.on('connect')
def handle_connect():
    print(f'User connected: {session.get("username", "Guest")}')

@socketio.on('get_home_page')
def handle_get_home_page():
    emit('home_page', {'message': 'Welcome to the LGS Stock Checker!'})
