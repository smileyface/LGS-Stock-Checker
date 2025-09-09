import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from data.database.db_config import engine
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
    Base.metadata.create_all(bind=engine)