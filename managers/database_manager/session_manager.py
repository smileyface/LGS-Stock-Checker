import os
from functools import wraps

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from utility.logger import logger

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@db:5432/lgs_stock_checker")

# SQLAlchemy Setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def get_session():
    """Returns a new database session."""
    return SessionLocal()

def db_query(func):
    """Decorator to manage database session scope for queries."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        session = SessionLocal()  # Open a new session
        try:
            result = func(*args, **kwargs, session=session)  # Pass session to function
            if isinstance(result, list):  # If returning multiple ORM objects
                session.expunge_all()  # Detach before session closes
            elif result is not None:
                session.expunge(result)  # Detach single ORM object
            session.commit()  # Commit if no errors
            return result
        except Exception as e:
            session.rollback()  # Rollback changes if error occurs
            logger.error(f"❌ Database query failed: {str(e)}")
            raise
        finally:
            session.close()  # Close session safely

    return wrapper