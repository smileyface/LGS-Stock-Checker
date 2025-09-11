import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from data.database.models.orm_models import Base

# The DATABASE_URL is expected to be provided by the environment (e.g., from docker-compose.yml).
DATABASE_URL = os.environ.get("DATABASE_URL")

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