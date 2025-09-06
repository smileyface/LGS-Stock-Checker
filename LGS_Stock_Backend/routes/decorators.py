from functools import wraps
from flask import session, redirect, url_for, request, jsonify

from managers.socket_manager import log_and_emit


def login_required(f):
    """Ensures a user is logged in before accessing a view."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            log_and_emit("warning", f"⚠️ Unauthorized access attempt to {request.path} from IP {request.remote_addr}")
            # For API endpoints that expect JSON, return a 401 error
            if request.path.startswith('/account/update'):
                return jsonify({"error": "User not logged in"}), 401
            # For all other pages, redirect to the login page
            return redirect(url_for('user_bp.login'))
        return f(*args, **kwargs)
    return decorated_function
