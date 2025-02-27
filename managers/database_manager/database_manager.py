import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from managers.database_manager.tables import Base

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@db:5432/lgs_stock_checker")

# SQLAlchemy Setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    """Initialize the database schema."""
    Base.metadata.create_all(bind=engine)

def get_session():
    """Returns a new database session."""
    return SessionLocal()
