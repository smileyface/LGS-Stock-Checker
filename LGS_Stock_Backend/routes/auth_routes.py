from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_login import login_user, logout_user, login_required, current_user

from managers import user_manager
from managers.socket_manager import log_and_emit

from flask import jsonify


auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/api/login', methods=['GET', 'POST'])
def login():
    """Handles user login."""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # FIX: Call the updated authenticate_user function
        user_data = user_manager.authenticate_user(username, password)
        
        if user_data:
            # 1. Get the user's ID from the returned schema
            user_id = user_data.id
            
            # 2. Use the implemented loader function to get the FlaskLoginUser object
            user = user_manager.load_user_by_id(user_id)
            
            # 3. Log the user in with Flask-Login
            login_user(user) 

            # Optional cleanup of old session key
            if "username" in session:
                 del session["username"] 

            log_and_emit("info", f"✅ User '{username}' logged in successfully.")
            return redirect(url_for("home_bp.dashboard")) # Assuming 'home_bp'
            
        log_and_emit("warning", f"⚠️ Failed login attempt for username '{username}'.")
        return render_template("landing.html", error="Invalid credentials")

    return render_template("landing.html")

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
    # The `current_user` proxy from Flask-Login holds the ORM object.
    # The `to_dict()` method on the User model is designed to serialize the user's
    # data, including a simple list of store slugs, which is exactly what the frontend needs.
    return jsonify(current_user.to_dict())
