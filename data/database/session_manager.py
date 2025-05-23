from functools import wraps

from data.database.db_config import SessionLocal
from utility.logger import logger


def db_query(func):
    """Decorator to manage database session scope for repositories."""

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
            pass  # No explicit close needed here
            logger.debug("🔍 Database session scope finished for db_query decorator.")

    return wrapper
