from typing import Optional
from schema import db
from data.database.session_manager import db_query
from data.database.models.orm_models import Store
from utility import logger


@db_query
def get_store_metadata(slug: str, session) -> Optional[db.StoreSchema]:
    """Fetch store details from the database and return it as a dictionary."""
    store_orm = session.query(Store).filter(Store.slug == slug).first()
    if store_orm:
        return db.StoreSchema.model_validate(store_orm)
    return None


@db_query
def get_all_stores(session) -> list[db.StoreSchema]:
    """Fetch all available stores."""
    stores = session.query(Store).all()
    logger.debug(f"Found {len(stores)} stores in the database.")
    return [db.StoreSchema.model_validate(store) for store in stores]
