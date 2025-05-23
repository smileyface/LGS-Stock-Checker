from data import schema
from data.database.session_manager import db_query
from data.models.orm_models import Store


@db_query
def get_store_metadata(slug, session) -> schema.StoreSchema:
    """Fetch store details from the database and return it as a dictionary."""
    return schema.StoreSchema.model_validate(session.query(Store).filter(Store.slug == slug).first())


@db_query
def get_all_stores(session) -> list[schema.StoreSchema]:
    """Fetch all available stores."""
    stores = session.query(Store).all()
    return [schema.StoreSchema.model_validate(store) for store in stores]
