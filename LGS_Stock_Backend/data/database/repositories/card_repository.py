from typing import List, Dict, Any
from sqlalchemy.orm import joinedload

# Internal package imports
from .. import schema
from ..session_manager import db_query
from ..models.orm_models import User, UserTrackedCards, Card, CardSpecification

# Project package imports
from utility import logger


@db_query
def get_users_cards(username: str, session) -> List[schema.UserTrackedCardSchema]:
    """
    Retrieves all tracked cards for a given user using an efficient single query.
    """
    logger.debug(f"📖 Querying for all tracked cards for user '{username}'.")
    user = (
        session.query(User)
        .filter(User.username == username)
        .options(
            joinedload(User.cards).joinedload(UserTrackedCards.specifications)
        )
        .first()
    )

    if not user:
        logger.warning(f"🚨 User '{username}' not found. Cannot retrieve cards.")
        return []

    logger.info(f"✅ Found {len(user.cards)} tracked cards for '{username}'.")
    return [schema.UserTrackedCardSchema.model_validate(card) for card in user.cards]


@db_query
def add_user_card(username: str, card_name: str, amount: int, card_specs: List[Dict[str, Any]], session) -> None:
    """
    Adds or updates a tracked card for a user, including its specifications.
    This function handles finding the user, finding/creating the card in the global
    card table, and then creating/updating the user-specific tracking information.
    """
    if not card_name:
        logger.warning("🚨 Attempted to add a card with no name. Operation aborted.")
        return

    user = session.query(User).filter(User.username == username).first()
    if not user:
        logger.warning(f"🚨 User '{username}' not found. Cannot add card.")
        return

    # Find or create the global card entry (ensures referential integrity)
    card_entry = session.query(Card).filter(Card.name == card_name).first()
    if not card_entry:
        logger.info(f"➕ Adding new card '{card_name}' to the global card table.")
        card_entry = Card(name=card_name)
        session.add(card_entry)
        session.flush()  # Ensure it gets an ID before proceeding

    # Find or create the user's tracked card entry
    tracked_card = session.query(UserTrackedCards).filter(
        UserTrackedCards.user_id == user.id,
        UserTrackedCards.card_name == card_name
    ).first()

    if tracked_card:
        logger.info(f"🔄 User '{username}' is already tracking '{card_name}'. Updating amount and specifications.")
        tracked_card.amount = amount  # Update amount if card is already tracked
    else:
        logger.info(f"➕ User '{username}' is now tracking '{card_name}'.")
        tracked_card = UserTrackedCards(user_id=user.id, amount=amount, card_name=card_name)
        session.add(tracked_card)

    if card_specs:
        # Get all existing specs for this card at once to avoid N+1 queries
        existing_specs_query = session.query(CardSpecification).filter(CardSpecification.user_card_id == tracked_card.id)
        existing_specs_set = {
            (s.set_code, s.collector_number, s.finish) for s in existing_specs_query.all()
        }

        for spec_data in card_specs:
            spec_tuple = (
                spec_data.get("set_code"),
                spec_data.get("collector_number"),
                spec_data.get("finish")
            )
            if spec_tuple not in existing_specs_set:
                new_spec = CardSpecification(
                    user_card_id=tracked_card.id,
                    set_code=spec_tuple[0],
                    collector_number=spec_tuple[1],
                    finish=spec_tuple[2]
                )
                session.add(new_spec)
                logger.info(f"➕ Added new specification {spec_tuple} for '{card_name}'.")

    logger.info(f"✅ Successfully processed '{card_name}' for user '{username}'.")


@db_query
def delete_user_card(username: str, card_name: str, session) -> None:
    """
    Deletes a tracked card for a user in a single, efficient operation.
    """
    logger.info(f"🗑️ Attempting to delete tracked card '{card_name}' for user '{username}'.")

    # Create a subquery to find the user's ID
    user_subquery = session.query(User.id).filter(User.username == username).scalar_subquery()

    # Perform the delete using the subquery
    # synchronize_session=False is recommended for bulk deletes for performance.
    deleted_count = session.query(UserTrackedCards).filter(
        UserTrackedCards.user_id == user_subquery,
        UserTrackedCards.card_name == card_name
    ).delete(synchronize_session=False)

    if deleted_count == 0:
        # This could be because the user doesn't exist or they aren't tracking the card.
        logger.warning(f"⚠️ No tracked card named '{card_name}' found for user '{username}'. No action taken.")
    else:
        logger.info(f"✅ Successfully deleted {deleted_count} tracked card record for '{username}'.")


@db_query
def update_user_tracked_cards_list(username: str, card_list: List[Dict[str, Any]], session) -> None:
    """
    Replaces a user's entire tracked card list with a new one.
    This performs a "delete-all-then-insert-all" operation for the given user.
    """
    logger.info(f"🔄 Replacing entire tracked card list for user '{username}'.")
    user = session.query(User).filter(User.username == username).first()
    if not user:
        logger.warning(f"🚨 User '{username}' not found. Cannot update card list.")
        return

    # Bulk delete existing tracked cards for this user.
    # This will also cascade delete all associated CardSpecification records.
    session.query(UserTrackedCards).filter(UserTrackedCards.user_id == user.id).delete(synchronize_session=False)
    logger.debug(f"🗑️ Cleared existing tracked cards for '{username}'.")

    if not card_list:
        logger.info(f"✅ Cleared all card preferences for user '{username}' as the provided list was empty.")
        return

    # Bulk insert new card preferences
    new_tracked_cards = []
    for card_data in card_list:
        # Note: This assumes card_name is valid and doesn't re-verify against the `cards` table
        # for performance. The `add_user_card` flow is better for single additions.
        new_tracked_cards.append(
            UserTrackedCards(
                user_id=user.id,
                card_name=card_data["card_name"],
                amount=card_data.get("amount", 1)
            )
        )

    session.bulk_save_objects(new_tracked_cards)
    logger.info(f"✅ Successfully saved {len(card_list)} new tracked cards for user '{username}'.")


@db_query
def update_user_tracked_card_preferences(username: str, card_name: str, preference_updates: Dict[str, Any], session) -> None:
    """
    Updates specific preferences (e.g., amount) for a single tracked card.
    """
    logger.info(f"✏️ Updating preferences for card '{card_name}' for user '{username}'.")

    # Find the specific card tracked by the user in a single query
    tracked_card = (
        session.query(UserTrackedCards)
        .join(User)
        .filter(User.username == username, UserTrackedCards.card_name == card_name)
        .first()
    )

    if not tracked_card:
        logger.warning(f"🚨 Card '{card_name}' not found for user '{username}'. Cannot update preferences.")
        return

    # Update preferences based on the provided dictionary
    if "amount" in preference_updates:
        new_amount = preference_updates["amount"]
        if isinstance(new_amount, int) and new_amount > 0:
            tracked_card.amount = new_amount
            logger.debug(f"Updated amount to {new_amount} for '{card_name}'.")
        else:
            logger.warning(f"⚠️ Invalid amount '{new_amount}' provided. Must be a positive integer.")

    # This can be extended for other preferences in the future.
    # For example:
    # if "notify_on_availability" in preference_updates:
    #     card.notify_on_availability = preference_updates["notify_on_availability"]

    logger.info(f"✅ Preferences updated for card '{card_name}' for user '{username}'.")
