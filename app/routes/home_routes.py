from flask_socketio import SocketIO, emit
from flask import session, Blueprint, render_template, redirect, url_for

from managers.availability_manager.availability_manager import check_availability
from managers.socket_manager.socket_manager import log_and_emit, socketio

home_bp = Blueprint("home_bp", __name__)
@home_bp.route("/")
def landing_page():
    if "username" in session:
        log_and_emit("info", f"ℹ️ User {session['username']} is already logged in. Redirecting to dashboard")
        return redirect(url_for("home_bp.dashboard"))
    return render_template("landing.html")

@home_bp.route("/dashboard")
def dashboard():
    if "username" not in session:
        log_and_emit("info", f"ℹ️ No user is logged in. Redirecting to landing page")
        return redirect(url_for("home_bp.landing_page"))
    return render_template("dashboard.html",
                           username=session["username"],
                           card_availability=check_availability(session["username"]))

@socketio.on('get_home_page')
def handle_get_home_page():
    emit('home_page', {'message': 'Welcome to the LGS Stock Checker!'})
