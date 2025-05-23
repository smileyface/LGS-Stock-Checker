from data import schema
from data.database.session_manager import db_query
from data.models.orm_models import User, Store, user_store_preferences
from utility.logger import logger


@db_query
def get_user_by_username(username, session):
    """Fetch user details from the database."""
    return schema.UserSchema.model_validate(session.query(User).filter(User.username == username).first())


@db_query
def add_user(username, password_hash, session):
    """Insert a new user into the database."""
    new_user = User(username=username, password_hash=password_hash)
    session.add(new_user)
    session.commit()
    logger.info(f"✅ User {username} added to the database")
    return new_user


@db_query
def update_username(old_username, new_username, session):
    user = session.query(User).where(User.username == old_username).first()
    user.username = new_username
    session.commit()
    logger.info(f"✅ Username updated successfully: {old_username} → {new_username}")


@db_query
def update_password(username, password_hash, session):
    user = session.query(User).where(User.username == username).first()
    user.password = password_hash
    session.commit()
    logger.info(f"✅ Password for {username} updated successfully!")


@db_query
def get_user_stores(username, session):
    user = session.query(User).where(User.username == username).first()
    if not user:
        # Convert ORM objects to DTOs before returning
        return [schema.StoreSchema.model_validate(store) for store in user.selected_stores]


@db_query
def add_user_store(username, store, session):
    user = session.query(User).filter(User.username == username).first()
    store_obj = session.query(Store).filter(Store.slug == store).first()

    # Add the store to the user's preferences
    new_preference = user_store_preferences(user_id=user.id, store_id=store_obj.id)
    session.add(new_preference)
    session.commit()

    logger.info(f"✅ Added '{store}' to user '{username}' preferences.")
