import json
import os

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import StaticPool

from utility import logger
from .models.orm_models import Store, Base
from .session_manager import db_query, init_session

# These will be initialized by the app factory or test setup.
engine = None


def initialize_database(database_url: str, for_testing: bool = False):
    """
    Initializes the database engine and session factory.
    In testing, uses a StaticPool to ensure a single connection for in-memory DB.
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
    # To add or manage stores, please interact with the 'stores' table directly.
    logger.info(
        "✅ Skipping database seeding from JSON file. Store management is now handled directly in the database."
    )
    pass
