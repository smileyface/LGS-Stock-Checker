from .user_routes import user_bp
from .auth_routes import auth_bp
from .system_routes import system_bp


def register_blueprints(app):
    """Registers all application blueprints."""
    app.register_blueprint(user_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(system_bp)
