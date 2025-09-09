from .home_routes import home_bp
from .user_routes import user_bp

# It's crucial to import the engine and Base model to create tables.
# The path to the engine is inferred from the error traceback.
from LGS_Stock_Backend.data.database.session_manager import engine
from LGS_Stock_Backend.data.database.models.orm_models import Base


def register_blueprints(app):
    # This ensures that database tables are created when the app starts.
    # `create_all` is safe to run on every startup as it won't
    # re-create tables that already exist. This fixes the "no such table"
    # error, but does not solve the underlying data persistence issue.
    Base.metadata.create_all(bind=engine)
    app.register_blueprint(home_bp)
    app.register_blueprint(user_bp)
