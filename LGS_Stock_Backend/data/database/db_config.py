import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from data.database.models.orm_models import Base

# The database file should be located within the persistent volume.
# The volume is mounted at /app/LGS_Stock_Backend/data/database in the container.
DB_FILE_PATH = "LGS_Stock_Backend/data/database/lgs_stock.db"

# Default to a SQLite database file located inside the persistent volume.
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DB_FILE_PATH}")

engine = create_engine(DATABASE_URL)

# Use a scoped_session to ensure a unique session per thread/request
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

def get_session():
    """Provides a database session from the session factory."""
    return SessionLocal()

def init_db():
    """
    Initializes the database by creating all tables defined in the ORM models.
    This function is idempotent and can be safely called on every application startup.
    """
    # For SQLite, we must ensure the directory for the database file exists.
    # This is crucial for the first run when a persistent volume is empty.
    if DATABASE_URL.startswith("sqlite:///"):
        # Extract the path from the URL, ignoring the 'sqlite:///' prefix.
        db_file_path = DATABASE_URL[10:]
        # Get the directory part of the path.
        db_dir = os.path.dirname(db_file_path)
        # Create the directory if it doesn't exist.
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    Base.metadata.create_all(bind=engine)