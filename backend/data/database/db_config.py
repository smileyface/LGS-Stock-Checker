"""
Database configuration and initialization for the application.

This module handles the setup of the SQLAlchemy engine and session factory,
and ensures that the database schema is created and synchronized with the
application's store registry. It provides functions for initializing the
database connection, retrieving the engine, and performing startup tasks
like populating the `stores` table.
"""

from sqlalchemy import create_engine, exc
from sqlalchemy.pool import StaticPool

from managers.store_manager.stores import STORE_REGISTRY
from utility import logger
from .models.orm_models import Store, Base
from .session_manager import db_query, init_session

# These will be initialized by the app factory or test setup.
ENGINE = None


def initialize_database(database_url: str, for_testing: bool = False):
    """
    Initializes the database engine and session factory.
    In testing, uses a StaticPool to ensure a single connection for in-memory DB.
    """

    # pylint: disable=global-statement
    global ENGINE

    if ENGINE:
        # Avoid re-initialization.
        logger.info("⛃ Database already initialized. Skipping.")
        return

    logger.info(f"⛃ Initializing database with URL: {database_url}")
    try:
        if for_testing:
            ENGINE = create_engine(
                database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
        else:
            ENGINE = create_engine(database_url)
    except exc.SQLAlchemyError as e:
        logger.error(f"❌ Error initializing database: {e}")
        return

    init_session(ENGINE)
    logger.info("🔄 Creating database tables...")
    Base.metadata.create_all(bind=get_engine())


def get_engine():
    """Provides the database engine."""
    if not ENGINE:
        raise RuntimeError(
            "Database not initialized. Call initialize_database() first."
        )
    return ENGINE


def startup_database():
    """
    Ensures that all stores defined in the code's STORE_REGISTRY exist in the database.
    This is run once on application startup when this package is imported.
    It uses local imports to avoid circular dependencies between the data layer
    and the manager layer.
    """

    @db_query
    def _sync(session):
        logger.info("🔄 Synchronizing stores from code registry to database...")
        db_store_slugs = {s[0] for s in session.query(Store.slug).all()}

        new_stores_added = 0
        for slug, store_instance in STORE_REGISTRY.items():
            if slug not in db_store_slugs:
                logger.info(
                    f"➕ Adding new store to database: {store_instance.name} (slug: {slug})"
                )
                new_store = Store(
                    name=store_instance.name,
                    slug=store_instance.slug,
                    homepage=store_instance.homepage,
                    search_url=store_instance.search_url,
                    fetch_strategy=store_instance.fetch_strategy,
                )
                session.add(new_store)
                new_stores_added += 1

        if new_stores_added > 0:
            logger.info(f"✅ Added {new_stores_added} new stores to the database.")
        else:
            logger.info(
                "✅ Database stores are already up-to-date with the code registry."
            )

    _sync(None)
