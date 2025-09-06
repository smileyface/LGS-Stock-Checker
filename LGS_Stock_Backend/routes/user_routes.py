from flask import session, request, Blueprint, redirect, render_template, url_for

from managers.store_manager.stores import STORE_REGISTRY
from managers.user_manager import update_selected_stores
from managers.user_manager.user_auth import update_password, authenticate_user
from managers.user_manager.user_manager import add_user, get_user, update_username

user_bp = Blueprint("user_bp", __name__)


@user_bp.route("/account")
def account_settings():
    if "username" not in session:
        return redirect(url_for("landing_page"))
    return render_template("account_settings.html",
                           username=session["username"],
                           stores=get_user(session["username"]).get("selected_stores", []),
                           all_stores=list(STORE_REGISTRY.keys()))


@user_bp.route("/account/update_stores", methods=["POST"])
def update_stores():
    username = session.get("username")
    if username:
        selected_stores = request.json.get("stores", [])
        update_selected_stores(username, selected_stores)
        return {"message": "Stores updated successfully"}
    return {"error": "User not logged in"}, 401


@user_bp.route("/account/update_username", methods=["POST"])
def change_username():
    username = session.get("username")
    new_username = request.json.get("new_username")
    if username and new_username:
        update_username(username, new_username)
        session["username"] = new_username
        return {"message": "Username updated successfully"}
    return {"error": "Invalid request"}, 400


@user_bp.route("/account/update_password", methods=["POST"])
def change_password():
    username = session.get("username")
    current_password = request.json.get("current_password")
    new_password = request.json.get("new_password")
    if username and current_password and new_password:
        if update_password(username, current_password, new_password):
            return {"message": "Password updated successfully"}
        return {"error": "Incorrect current password"}, 400
    return {"error": "Invalid request"}, 400


@user_bp.route("/login", methods=["GET", "POST"])
def login():
    """Handles user login."""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = authenticate_user(username, password)
        if user:
            session["username"] = username
            return redirect(url_for("home_bp.dashboard"))

        return render_template("landing.html", error="Invalid credentials")

    return render_template("landing.html")


@user_bp.route("/logout")
def logout():
    """Logs the user out and redirects to the landing page."""
    session.clear()
    return redirect(url_for("home_bp.landing_page"))


@user_bp.route("/create_account", methods=["GET", "POST"])
def create_account():
    """Handles user registration."""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return render_template("create_account.html", error="Username and password are required")

        if get_user(username):
            return render_template("create_account.html", error="Username already exists")

        add_user(username, password)
        session["username"] = username
        return redirect(url_for("home_bp.dashboard"))

    return render_template("create_account.html")
