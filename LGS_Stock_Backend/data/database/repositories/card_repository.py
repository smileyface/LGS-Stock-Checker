from sqlalchemy.orm import joinedload

from data.database import schema
from data.database.session_manager import db_query
from data.database.models.orm_models import User, UserTrackedCards, Card, CardSpecification
from data.database.repositories.user_repository import get_user_by_username
from utility.logger import logger


@db_query
def get_users_cards(username, session) -> list[schema.UserTrackedCardSchema]:
    """
    Retrieves all tracked cards for a given user.
    """
    user_id = session.query(User.id).filter(User.username == username).scalar()

    if not user_id:
        logger.warning(f"🚨 User '{username}' not found. Cannot retrieve cards.")
        return []

    # Fetch all user card preferences
    cards = (
        session.query(UserTrackedCards)
        .filter(UserTrackedCards.user_id == user_id)
        .options(joinedload(UserTrackedCards.specifications))  # Eager load
        .all()
    )
    logger.info(f"✅ Got {len(cards)} cards for {username}")
    return [
        schema.UserTrackedCardSchema(
            card_name=card.card_name,
            amount=card.amount,
            specifications=[schema.CardSpecificationSchema.model_validate(spec) for spec in card.specifications]
        )
        for card in cards
    ]


@db_query
def add_user_card(username, card_name, amount, card_specs, session):
    """
    Adds a new tracked card for a user, along with its specifications if applicable.

    :param username: The username of the user tracking the card.
    :param card_name: The name of the card being tracked.
    :param card_specs: A list of specifications (set code, finish, etc.) for the card.
    :param session: SQLAlchemy session (handled by the @db_query decorator).
    """
    # Add a guard clause to prevent adding a card with no name.
    if not card_name:
        logger.warning("🚨 Attempted to add a card with no name. Operation aborted.")
        return

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
        return

    # Check if the user is already tracking this card
    existing_card = session.query(UserTrackedCards).filter(
        UserTrackedCards.user_id == user.id,
        UserTrackedCards.card_name == card_name
    ).first()

    if existing_card:
        logger.info(f"🔄 User '{username}' is already tracking '{card_name}', updating specifications.")
    else:
        # Create a new tracked card entry
        existing_card = UserTrackedCards(user_id=user.id, amount=amount, card_name=card_name)
        session.add(existing_card)
        session.flush()  # Flush to ensure 'existing_card.id' is populated before use.

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


@db_query
def delete_user_card(username, card_name, session):
    user_id = session.query(User.id).filter(User.username == username).scalar()

    if not user_id:
        logger.warning(f"🚨 User '{username}' not found. Cannot delete cards.")
        return []

    deleted = session.query(UserTrackedCards).filter(
        UserTrackedCards.user_id == user_id,
        UserTrackedCards.card_name == card_name).delete()

    if deleted == 0:
        logger.warning(f"🚨 '{card_name}' not found for user '{username}'.")

    logger.info(f"✅Deleted {deleted} record(s) for user '{username}' and card '{card_name}'.")


@db_query
def update_user_tracked_cards_list(username, card_list, session):
    """
    Updates the user's card preferences in the database.

    Args:
        username (str): The username of the user.
        card_list (list of dict): A list of card preferences (card_name, set_code, finish).
        session (Session): SQLAlchemy session.
    """
    # Fetch user ORM object directly to get its ID
    user = session.query(User).filter(User.username == username).first()
    if not user:
        logger.warning(f"🚨 User '{username}' not found in the database.")
        return

    # Remove existing card preferences for this user
    session.query(UserTrackedCards).filter(UserTrackedCards.user_id == user.id).delete()

    if not card_list:
        logger.info(f"✅ Cleared all card preferences for user '{username}' as the provided list was empty.")
        return

    # Insert new card preferences
    for card in card_list:
        new_pref = UserTrackedCards(
            user_id=user.id,
            card_name=card["card_name"],
            amount=card.get("amount", 1)  # Default amount to 1 if not provided
        )
        session.add(new_pref)

    logger.info(f"✅ Updated card preferences for user '{username}' with {len(card_list)} cards.")


@db_query
def update_user_tracked_card_preferences(username, card_name, preference, session):
    user = session.query(User).filter(User.username == username).first()
    if not user:
        logger.warning(f"🚨 User '{username}' not found. Cannot update card preferences.")
        return

    card = session.query(UserTrackedCards).filter(
        UserTrackedCards.user_id == user.id,
        UserTrackedCards.card_name == card_name
    ).first()

    if not card:
        logger.warning(f"🚨 Card '{card_name}' not found for user '{username}'. Cannot update preferences.")
        return

    # Update preferences
    if "amount" in preference:
        card.amount = preference["amount"]

    # You can extend this block for other preferences too
    # if "notify_on_availability" in preference:
    #     card.notify_on_availability = preference["notify_on_availability"]

    logger.info(f"✅Updated preferences for card '{card_name}' for user '{username}'.")
