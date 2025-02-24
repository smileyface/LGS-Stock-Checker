from .availability_routes import availability_bp
from .home_routes import home_bp
from .home_routes import home_bp
from .user_routes import user_bp


def register_blueprints(app):
    app.register_blueprint(home_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(availability_bp)
