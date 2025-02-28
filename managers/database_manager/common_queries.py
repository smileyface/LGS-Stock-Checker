from sqlalchemy import text

from managers.database_manager.database_manager import get_session
from managers.database_manager.session_manager import db_query
from managers.database_manager.tables import User, Card, Store
from utility.logger import logger


# --- USER QUERIES ---
@db_query
def get_user_by_username(username, session):
    """Fetch user details from the database."""
    return session.query(User).where(User.username == username).first()


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
def get_users_stores(username, session):
    user = session.query(User).where(User.username == username).first()
    if not user:
        return []
    return user.selected_stores  # This uses the relationship defined in the SQLAlchemy model


# --- CARD QUERIES ---
def get_cards_by_name(card_name):
    """Fetch cards using raw SQL."""
    session = get_session()
    query = text("SELECT * FROM cards WHERE name = :card_name")
    result = session.execute(query, {"card_name": card_name})
    cards = result.fetchall()
    session.close()
    return cards


def get_all_cards():
    """Fetch all cards in the database."""
    session = get_session()
    cards = session.query(Card).all()
    session.close()
    return cards


# --- STORE QUERIES ---

@db_query
def get_store_metadata(slug, session):
    """Fetch store details from the database."""
    store = session.execute("SELECT * FROM stores WHERE slug = :slug", {"slug": slug}).fetchone()
    return dict(store) if store else None


def get_all_stores():
    """Fetch all available stores."""
    session = get_session()
    stores = session.query(Store).all()
    session.close()
    return stores
