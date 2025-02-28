from functools import wraps
from managers.database_manager.database_manager import get_session

def db_query(func):
    """Decorator to manage SQLAlchemy sessions for database queries."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        session = get_session()
        try:
            result = func(*args, **kwargs, session=session)  # Pass session into function
            session.commit()  # Commit changes if any
            return result
        except Exception as e:
            session.rollback()  # Rollback on error
            raise e
        finally:
            session.close()  # Ensure session is closed
    return wrapper