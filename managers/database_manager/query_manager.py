from sqlalchemy import text
from managers.database_manager.database_manager import get_session
from managers.database_manager.tables import User, Card, Store
# --- USER QUERIES ---
def get_user_by_username(username):
    """Fetch user details from the database."""
    session = get_session()
    user = session.query(User).filter(User.username == username).first()
    session.close()
    return user

def add_user(username, password_hash):
    """Insert a new user into the database."""
    session = get_session()
    new_user = User(username=username, password_hash=password_hash)
    session.add(new_user)
    session.commit()
    session.close()
    return new_user


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
def get_store_by_name(store_name):
    """Fetch a store by its name."""
    session = get_session()
    store = session.query(Store).filter(Store.name == store_name).first()
    session.close()
    return store

def get_all_stores():
    """Fetch all available stores."""
    session = get_session()
    stores = session.query(Store).all()
    session.close()
    return stores
