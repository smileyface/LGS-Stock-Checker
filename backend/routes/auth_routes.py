from flask import Blueprint, request, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user

from managers import user_manager
from managers import socket_manager


auth_bp = Blueprint("auth_bp", __name__)


@auth_bp.route("/api/login", methods=["POST"])
def login():

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = user_manager.authenticate_user(username, password)

    if user:
        # The user object returned from a successful authentication
        # is the ORM object that Flask-Login needs.
        login_user(user)

        # Optional cleanup of old session key
        if "username" in session:
            del session["username"]

        socket_manager.log_and_emit(
            "info", f"✅ User '{username}' logged in successfully."
        )
        return jsonify({"message": "Login successful"}), 200

    socket_manager.log_and_emit(
        "warning", f"⚠️ Failed login attempt for username '{username}'."
    )
    return jsonify({"error": "Invalid credentials"}), 401


@auth_bp.route("/api/register", methods=["POST"])
def register():
    """Handles new user registration."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    # The user_manager.add_user function handles checking for existing users
    # and returns False if the user already exists.
    success = user_manager.add_user(username, password)

    if success:
        socket_manager.log_and_emit(
            "info", f"✅ New user '{username}' registered successfully."
        )
        # HTTP 201 Created is the standard response for a successful creation
        return jsonify({"message": "User registered successfully"}), 201
    else:
        socket_manager.log_and_emit(
            "warning",
            f"⚠️ Failed registration attempt for username '{username}'"
            f" (already exists).",
        )
        return (
            jsonify({"error": "Username already exists"}),
            409,
        )  # HTTP 409 Conflict


@auth_bp.route("/api/logout", methods=["POST"])
@login_required
def logout():
    """Handles user logout."""
    # Optional cleanup of old session key, if it exists
    if "username" in session:
        del session["username"]

    socket_manager.log_and_emit(
        "info", f"✅ User '{current_user.username}' logged out successfully."
    )
    logout_user()
    return jsonify({"message": "Logout successful"}), 200


@auth_bp.route("/api/user_data", methods=["GET"])
@login_required
def user_data():
    """
    Provides data for the currently authenticated user.
    The @login_required decorator ensures this route is protected.
    If the user is not logged in, Flask-Login will automatically
    return a 401 Unauthorized error, which the frontend handles.
    """
    # The `current_user` proxy from Flask-Login holds the ORM object.
    # The `to_dict()` method on the User model is designed to serialize
    # the user's data, including a simple list of store slugs, which is
    # exactly what the frontend needs.
    return jsonify(current_user.to_dict())
