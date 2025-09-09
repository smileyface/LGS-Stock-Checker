from .home_routes import home_bp
from .user_routes import user_bp
from data.database import init_db


def register_blueprints(app):
    """Initializes the database and registers all application blueprints."""
    # Initialize the database, creating tables if they don't exist.
    init_db()

    app.register_blueprint(home_bp)
    app.register_blueprint(user_bp)
