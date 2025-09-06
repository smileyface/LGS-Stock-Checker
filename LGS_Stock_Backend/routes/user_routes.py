from flask import session, request, Blueprint, redirect, render_template, url_for

from managers.store_manager.stores import STORE_REGISTRY
from managers.user_manager import update_selected_stores
from managers.socket_manager import log_and_emit
from managers.user_manager.user_auth import update_password, authenticate_user
from managers.user_manager.user_manager import add_user, get_user, update_username
from .decorators import login_required

user_bp = Blueprint("user_bp", __name__)


@user_bp.route("/account")
@login_required
def account_settings():
    return render_template("account_settings.html",
                           username=session["username"],
                           stores=get_user(session["username"]).get("selected_stores", []),
                           all_stores=list(STORE_REGISTRY.keys()))


@user_bp.route("/account/update_stores", methods=["POST"])
@login_required
def update_stores():
    username = session.get("username")
    selected_stores = request.json.get("stores", [])
    update_selected_stores(username, selected_stores)
    return {"message": "Stores updated successfully"}


@user_bp.route("/account/update_username", methods=["POST"])
@login_required
def change_username():
    username = session.get("username")
    new_username = request.json.get("new_username")
    if not new_username:
        return {"error": "New username is required"}, 400
    update_username(username, new_username)
    session["username"] = new_username
    return {"message": "Username updated successfully"}


@user_bp.route("/account/update_password", methods=["POST"])
@login_required
def change_password():
    username = session.get("username")
    current_password = request.json.get("current_password")
    new_password = request.json.get("new_password")
    if not (current_password and new_password):
        return {"error": "Both current and new passwords are required"}, 400
    if update_password(username, current_password, new_password):
        return {"message": "Password updated successfully"}
    return {"error": "Incorrect current password"}, 400


@user_bp.route("/login", methods=["GET", "POST"])
def login():
    """Handles user login."""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = authenticate_user(username, password)
        if user:
            session["username"] = username
            log_and_emit("info", f"✅ User '{username}' logged in successfully.")
            return redirect(url_for("home_bp.dashboard"))

        log_and_emit("warning", f"⚠️ Failed login attempt for username '{username}'.")
        return render_template("landing.html", error="Invalid credentials")

    return render_template("landing.html")


@user_bp.route("/logout")
def logout():
    """Logs the user out and redirects to the landing page."""
    username = session.get("username", "unknown")
    session.clear()
    log_and_emit("info", f"👋 User '{username}' logged out.")
    return redirect(url_for("home_bp.landing_page"))


@user_bp.route("/create_account", methods=["GET", "POST"])
def create_account():
    """Handles user registration."""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            log_and_emit("warning", "⚠️ Account creation failed: Username or password missing.")
            return render_template("create_account.html", error="Username and password are required")

        if get_user(username):
            log_and_emit("warning", f"⚠️ Account creation failed: Username '{username}' already exists.")
            return render_template("create_account.html", error="Username already exists")

        add_user(username, password)
        session["username"] = username
        log_and_emit("info", f"🎉 New account created for user '{username}'.")
        return redirect(url_for("home_bp.dashboard"))

    return render_template("create_account.html")
