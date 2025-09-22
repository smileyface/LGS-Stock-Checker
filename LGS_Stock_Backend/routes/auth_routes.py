from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user

from managers import user_manager

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/api/login', methods=['POST'])
def login():
    """Handles user login."""
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"error": "Username and password are required"}), 400

    user = user_manager.authenticate_user(data['username'], data['password'])

    if user:
        login_user(user, remember=True) # 'remember=True' creates a persistent session
        return jsonify({"message": "Login successful"}), 200
    
    return jsonify({"error": "Invalid username or password"}), 401

@auth_bp.route('/api/logout', methods=['POST'])
@login_required
def logout():
    """Handles user logout."""
    logout_user()
    return jsonify({"message": "Logout successful"}), 200

@auth_bp.route('/api/user_data', methods=['GET'])
@login_required
def user_data():
    """
    Provides data for the currently authenticated user.
    The @login_required decorator ensures this route is protected.
    If the user is not logged in, Flask-Login will automatically
    return a 401 Unauthorized error, which the frontend handles.
    """
    # By using the manager, we adhere to the separation of concerns.
    # The manager returns a Pydantic schema (DTO), which is safe to use.
    user_dto = user_manager.get_public_user_profile(current_user.username)
    if not user_dto:
        return jsonify({"error": "User not found"}), 404

    # Pydantic's .model_dump() is the modern equivalent of .dict()
    return jsonify(user_dto.model_dump())
