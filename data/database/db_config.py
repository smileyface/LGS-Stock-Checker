import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

# This will be the connection string for your actual database (e.g., PostgreSQL)
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./lgs_stock_checker.db")

engine = create_engine(DATABASE_URL)

# Use a scoped_session to ensure a unique session per thread/request
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

def get_session():
    """Provides a database session from the session factory."""
    return SessionLocal()