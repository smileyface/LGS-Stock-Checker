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


def get_engine():
    """Provides the database engine."""
    if not engine:
        raise RuntimeError("Database not initialized. Call initialize_database() first.")
    return engine

def startup_database():
    """
    Seeds the database with store information from a configuration file.

    This function reads from `stores.json` and ensures that each store
    defined there exists in the `stores` table in the database. It uses the
    `platform` key from the JSON to set the `fetch_strategy` in the database.
    """

    @db_query
    def _sync(session):
        logger.info("🔄 Synchronizing stores from config file to database...")
        db_store_slugs = {s[0] for s in session.query(Store.slug).all()}
        
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'managers', 'store_manager', 'stores', 'stores.json')
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                stores_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"❌ Could not load or parse stores.json for seeding: {e}")
            return

        new_stores_added = 0
        for store_data in stores_data:
            if store_data['slug'] not in db_store_slugs:
                logger.info(f"➕ Seeding new store to database: {store_data['name']} (slug: {store_data['slug']})")
                new_store = Store(
                    name=store_data['name'],
                    slug=store_data['slug'],
                    homepage=store_data['homepage'],
                    search_url=f"{store_data['homepage'].strip('/')}/products/search",
                    fetch_strategy=store_data['platform'],
                )
                session.add(new_store)
                new_stores_added += 1

        if new_stores_added > 0:
            logger.info(f"✅ Added {new_stores_added} new stores to the database.")
        else:
            logger.info("✅ Database stores are already up-to-date with config file.")
    _sync(None)
