from managers.database_manager.session_manager import engine
from managers.database_manager.tables import Base


def init_db():
    """Initialize the database schema."""
    Base.metadata.create_all(bind=engine)
