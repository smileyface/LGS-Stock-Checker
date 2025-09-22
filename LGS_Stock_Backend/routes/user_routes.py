from flask import session, request, Blueprint, render_template

from managers import store_manager
from managers import user_manager
from managers import socket_manager
from .decorators import login_required

user_bp = Blueprint("user_bp", __name__)


@user_bp.route("/account")
@login_required
def account_settings():
    user = user_manager.get_user(session["username"])
    # The user object is a Pydantic model, so we use attribute access.
    # Provide a default empty list if the user is not found for any reason.
    stores = user.selected_stores if user else []
    return render_template("account_settings.html",
                           username=session["username"],
                           stores=stores,
                           all_stores=list(store_manager.STORE_REGISTRY.keys()))


@user_bp.route("/account/update_stores", methods=["POST"])
@login_required
def update_stores():
    username = session.get("username")
    selected_stores = request.json.get("stores", [])
    user_manager.update_selected_stores(username, selected_stores)
    return {"message": "Stores updated successfully"}


@user_bp.route("/account/update_username", methods=["POST"])
@login_required
def change_username():
    username = session.get("username")
    new_username = request.json.get("new_username")
    if not new_username:
        return {"error": "New username is required"}, 400
    user_manager.update_username(username, new_username)
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
    if user_manager.update_password(username, current_password, new_password):
        return {"message": "Password updated successfully"}
    return {"error": "Incorrect current password"}, 400
