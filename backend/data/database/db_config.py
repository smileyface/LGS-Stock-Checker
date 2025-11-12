"""
Database configuration and initialization utilities.

This module provides helpers to create and manage the SQLAlchemy Engine and
initialize the application's database schema. It is intended to be called once
during application startup (or during test setup) to configure the engine and
session factory, create tables from ORM models, and provide access to the
engine for other modules.

Public API:
- initialize_database(database_url: str, for_testing: bool = False)
    Create and configure the SQLAlchemy engine and initialize the session
    factory. If called when the engine is already initialized, it is a no-op
    and logs that initialization is being skipped. When for_testing is True,
    the engine is created with a StaticPool and connect_args=
    {"check_same_thread": False}
    to support in-memory SQLite usage across multiple connections in tests.
    After engine creation, init_session(engine) is invoked and
    Base.metadata.create_all()
    is called to ensure ORM tables exist. Errors during engine creation are
    logged, and the function returns early on error.

    Parameters:
    - database_url (str): SQLAlchemy database URL (e.g. "sqlite:///db.sqlite"
      or "sqlite:///:memory:").
    - for_testing (bool): If True, configures engine for test usage
     (StaticPool).
    - Side effects: sets the module-level engine, initializes sessions, and
      creates database tables.

- get_engine() -> Engine
    Return the initialized SQLAlchemy engine. Raises RuntimeError if
    initialize_database() has not been called yet.

    Raises:
    - RuntimeError: when called before engine initialization.

- startup_database()
    Placeholder for startup tasks related to the database. Historically used to
    seed store data from a JSON file; seeding has been intentionally removed so
    the database is the single source of truth for store information. This
    function currently logs that seeding is skipped and is preserved for future
    startup tasks.

Module variables:
- engine: The module-level SQLAlchemy Engine instance (initially None). After
  successful initialization via initialize_database(), this holds the Engine.

Notes:
- The module depends on external symbols:
    - Base (ORM declarative base) whose metadata will be used to create tables.
    - init_session(engine) to configure the session factory for the
    application.
- Logging is performed via the imported logger to surface progress and errors.
- The function is idempotent: repeated calls to initialize_database() will be
  ignored once an engine is set.

"""

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import StaticPool

from utility import logger
from .models.orm_models import Base
from .session_manager import init_session

# These will be initialized by the app factory or test setup.
engine = None


def initialize_database(database_url: str, for_testing: bool = False):
    """
    Initializes the database engine and session factory.
    In testing, uses a StaticPool to ensure a single connection
    for in-memory DB.
    """

    global engine

    if engine:
        # Avoid re-initialization.
        logger.info("⛃ Database already initialized. Skipping.")
        return

    logger.info(f"⛃ Initializing database with URL: {database_url}")
    try:
        if for_testing:
            engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
        else:
            engine = create_engine(database_url)
    except SQLAlchemyError as e:
        logger.error(f"❌ Error initializing database: {e}")
        return

    init_session(engine)
    logger.info("🔄 Creating database tables...")
    Base.metadata.create_all(bind=get_engine())
    logger.info("✅ Database tables created successfully.")


def get_engine():
    """Provides the database engine."""
    if not engine:
        raise RuntimeError(
            "Database not initialized. Call initialize_database() first."
        )
    return engine


def startup_database():
    """
    Seeds the database with initial data. This function is preserved for future
    startup tasks but the store seeding from stores.json has been removed
    to make the database the single source of truth for store data.
    """
    # The logic to seed stores from stores.json has been intentionally removed.
    # The database is now the single source of truth for store information.
    # To add or manage stores, please interact with the 'stores'
    # table directly.
    logger.info(
        "✅ Skipping database seeding from JSON file. "
        "Store management is now handled directly in the database."
    )
    pass
