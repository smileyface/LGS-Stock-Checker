from sqlalchemy import text

from managers.database_manager.session_manager import db_query, get_session
from managers.database_manager.tables import User, Card, Store, UserTrackedCards, user_store_preferences, \
    CardSpecification
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
def get_user_stores(username, session):
    user = session.query(User).where(User.username == username).first()
    if not user:
        return []
    return user.selected_stores  # This uses the relationship defined in the SQLAlchemy model


@db_query
def add_user_store(username, store, session):
    user = session.query(User).filter(User.username == username).first()
    store_obj = session.query(Store).filter(Store.slug == store).first()

    # Add the store to the user's preferences
    new_preference = user_store_preferences(user_id=user.id, store_id=store_obj.id)
    session.add(new_preference)
    session.commit()

    logger.info(f"✅ Added '{store}' to user '{username}' preferences.")
    return True


# --- CARD QUERIES ---
@db_query
def get_users_cards(username, session):
    """
    Retrieves all tracked cards for a given user.
    """
    user = session.query(User).filter(User.username == username).first()

    if not user:
        logger.warning(f"🚨 User '{username}' not found. Cannot retrieve cards.")
        return []

    # Fetch all user card preferences
    cards = session.query(UserTrackedCards).filter(UserTrackedCards.user_id == user.id).all()

    return cards


@db_query
def add_user_card(username, card_name, card_specs, session):
    """
    Adds a new tracked card for a user, along with its specifications if applicable.

    :param username: The username of the user tracking the card.
    :param card_name: The name of the card being tracked.
    :param card_specs: A list of specifications (set code, finish, etc.) for the card.
    :param session: SQLAlchemy session (handled by the @db_query decorator).
    """
    # Ensure the card exists in the cards table
    card_entry = session.query(Card).filter(Card.name == card_name).first()

    if not card_entry:
        logger.info(f"➕ Adding new card '{card_name}' to the database.")
        card_entry = Card(name=card_name)
        session.add(card_entry)
        session.flush()  # Ensure it gets an ID before proceeding

    # Fetch the user from the database
    user = session.query(User).filter(User.username == username).first()

    if not user:
        logger.warning(f"🚨 User '{username}' not found. Cannot add card.")
        return False

    # Check if the user is already tracking this card
    existing_card = session.query(UserTrackedCards).filter(
        UserTrackedCards.user_id == user.id,
        UserTrackedCards.card_name == card_name
    ).first()

    if existing_card:
        logger.info(f"🔄 User '{username}' is already tracking '{card_name}', updating specifications.")
    else:
        # Create a new tracked card entry
        existing_card = UserTrackedCards(user_id=user.id, card_name=card_name)
        session.add(existing_card)

    if card_specs:
        # Ensure card_specs is a list
        if not isinstance(card_specs, list):
            card_specs = [card_specs]  # Convert single spec into a list

        # Add or update specifications
        for spec in card_specs:
            spec_entry = session.query(CardSpecification).filter_by(
                user_card_id=existing_card.id,
                set_code=spec.get("set_code"),
                finish=spec.get("finish"),
                collector_number=spec.get("collector_number")
            ).first()

            if not spec_entry:
                new_spec = CardSpecification(
                    user_card_id=existing_card.id,
                    set_code=spec.get("set_code"),
                    finish=spec.get("finish"),
                    collector_number=spec.get("collector_number")
                )
                session.add(new_spec)
                logger.info(f"➕ Added specification {spec} for '{card_name}'.")

    logger.info(f"✅ Successfully added/updated '{card_name}' for user '{username}'.")
    return True


@db_query
def update_user_tracked_cards(username, card_list, session):
    """
    Updates the user's card preferences in the database.

    Args:
        username (str): The username of the user.
        card_list (list of dict): A list of card preferences (card_name, set_code, finish).
        session (Session): SQLAlchemy session.
    """
    # Fetch user ID
    user = session.query(User).filter(User.username == username).first()
    if not user:
        logger.warning(f"🚨 User '{username}' not found in the database.")
        return

    # Remove existing card preferences
    session.query(UserTrackedCards).filter(UserTrackedCards.user_id == user.id).delete()

    # Insert new card preferences
    for card in card_list:
        new_pref = UserTrackedCards(
            user_id=user.id,
            card_name=card["card_name"]
        )
        session.add(new_pref)

    session.commit()
    logger.info(f"✅ Updated card preferences for user '{username}' with {len(card_list)} cards.")


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
    """Fetch store details from the database and return it as a dictionary."""
    return session.query(Store).filter(Store.slug == slug).first()


def get_all_stores():
    """Fetch all available stores."""
    session = get_session()
    stores = session.query(Store).all()
    session.close()
    return stores
