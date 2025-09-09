from typing import Optional
from data.database import schema
from data.database.session_manager import db_query
from data.database.models.orm_models import Store
from .. import schema
from ..session_manager import db_query
from ..models.orm_models import Store


@db_query
def get_store_metadata(slug: str, session) -> Optional[schema.StoreSchema]:
    """Fetch store details from the database and return it as a dictionary."""
    store_orm = session.query(Store).filter(Store.slug == slug).first()
    if store_orm:
        return schema.StoreSchema.model_validate(store_orm)
    return None


@db_query
def get_all_stores(session) -> list[schema.StoreSchema]:
    """Fetch all available stores."""
    stores = session.query(Store).all()
    return [schema.StoreSchema.model_validate(store) for store in stores]
