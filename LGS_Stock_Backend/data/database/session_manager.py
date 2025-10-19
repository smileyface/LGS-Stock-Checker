from functools import wraps
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import text

from utility import logger

SessionLocal = None

def db_query(func):
    """Decorator to manage database session scope for repositories."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        session = get_session()
        # Open a new session
        try:
            result = func(*args, **kwargs, session=session)  # Pass session to function
            session.commit()  # Commit if no errors
            return result
        except Exception as e:
            session.rollback()  # Rollback changes if error occurs
            logger.error(f"❌ Database query failed: {str(e)}")
            raise
        finally:
            SessionLocal.remove()  # Ensure the session is closed and returned to the pool
            logger.debug("🔍 Database session scope finished for db_query decorator.")

    return wrapper

def init_session(engine):
    """Initializes the database session factory."""
    global SessionLocal
    logger.info("🔄 Initializing database session factory...")

    try:
        SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False))
    except Exception as e:
        logger.error(f"❌ Error initializing database session factory: {e}")
        return
    
    # This check is unlikely to ever be true, as scoped_session raises exceptions on failure.
    # It's kept as a safeguard, but the real issue is likely an exception or early return.
    if not SessionLocal:
        logger.error("❌ Database not initialized.")
        return
    else:
        logger.info("✅ Database initialized successfully.")

def remove_session():
    """Remove the database session after each request to prevent leaks."""
    # This check prevents an error if the app is run without a DATABASE_URL,
    # in which case SessionLocal would be None.
    if SessionLocal:
        SessionLocal.remove()

def get_session():
    """Provides a database session from the session factory."""
    if not SessionLocal:
        raise RuntimeError("Database not initialized. Call initialize_database() first.")
    return SessionLocal()

@db_query
def health_check(session):
    try:
        session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"❌ Database Health check failed: {e}")
        return False
    finally:
        remove_session()