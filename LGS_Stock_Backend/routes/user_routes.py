from flask import request, Blueprint, jsonify
from flask_login import login_required, current_user

from managers import store_manager
from managers import user_manager

user_bp = Blueprint("user_bp", __name__)


@user_bp.route("/account/update_stores", methods=["POST"])
@login_required
def update_stores():
    selected_stores = request.json.get("stores", [])
    user_manager.update_selected_stores(current_user.username, selected_stores)
    return jsonify({"message": "Stores updated successfully"})


@user_bp.route("/account/update_username", methods=["POST"])
@login_required
def change_username():
    new_username = request.json.get("new_username")
    if not new_username:
        return jsonify({"error": "New username is required"}), 400
    # Note: Changing username with Flask-Login requires re-logging in the user
    # for the session to reflect the change immediately. This is a simplified version.
    user_manager.update_username(current_user.username, new_username)
    return jsonify({"message": "Username updated successfully"})


@user_bp.route("/account/update_password", methods=["POST"])
@login_required
def change_password():
    current_password = request.json.get("current_password")
    new_password = request.json.get("new_password")
    if not (current_password and new_password):
        return jsonify({"error": "Both current and new passwords are required"}), 400
    if user_manager.update_password(current_user.username, current_password, new_password):
        return jsonify({"message": "Password updated successfully"})
    return jsonify({"error": "Incorrect current password"}), 400

