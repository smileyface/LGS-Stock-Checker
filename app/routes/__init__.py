from flask import Blueprint
from .home_routes import home_bp
from .card_routes import card_bp
from .user_routes import user_bp
from .availability_routes import availability_bp

def register_blueprints(app):
    app.register_blueprint(home_bp)
    app.register_blueprint(card_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(availability_bp)
