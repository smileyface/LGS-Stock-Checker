from typing import List, Dict, Any, Optional
# SQLAlchemy imports
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.session import Session

# Internal package imports

from schema import orm
from ..session_manager import db_query
from .user_repository import get_user_orm_by_username
from .catalogue_repository import get_set, get_finish
from ..models import (
    Card,
    CardSpecification,
    UserTrackedCards,
)
from utility import logger


@db_query
def get_users_cards(
    username: str,
    *,
    session: Session
) -> List[orm.UserTrackedCardSchema]:
    assert session is not None, "Session is injected by @db_query decorator"
    """
    Retrieves all tracked cards for a given user using an
    efficient single query.
    """
    logger.debug(f"📖 Querying for all tracked cards for user '{username}'.")
    user = get_user_orm_by_username(username)

    if not user:
        logger.warning(f"User '{username}' not found. Cannot get cards.")
        return []

    if not user.cards:
        logger.warning(f"User '{username}' has no tracked cards.")
        return []
    else:
        logger.info(f"✅ Found {len(user.cards)} tracked cards \
                    for '{username}'.")
        return user.cards


@db_query
def add_card_to_user(
    username: str,
    card_data: Dict[str, Any],
    *,
    session: Session,
) -> None:
    assert session is not None, "Session is injected by @db_query decorator"
    """
    Adds or updates a tracked card for a user, including its specifications.
    This function handles finding the user, finding/creating the card in the
    global card table, and then creating/updating the user-specific tracking
      information.
    """
    valid_card_data = orm.UserTrackedCardSchema.model_validate(card_data)
    card_name = valid_card_data.card.name
    amount = valid_card_data.amount
    card_specs = valid_card_data.specifications
    if not card_name:
        logger.warning(
            "🚨 Attempted to add a card with no name. Operation aborted."
        )
        return

    user = get_user_orm_by_username(username)
    card_entry = get_card(card_name)

    if card_entry is None:
        # Logging for this error is handled in
        # search_card_names
        return

    if not user:
        # Logging for this error is handled in
        # search_card_names
        return

    # Find or create the user's tracked card entry
    tracked_card = get_tracked_card(username, card_name)

    if tracked_card:
        logger.info(
            f"🔄 User '{username}' is already tracking '{card_name}'. "
            f"Adding new specifications if any."
        )
        # Amount is not updated here; use `
        # update_user_tracked_card_preferences` for that.
    else:
        logger.info(f"➕ User '{username}' is now tracking '{card_name}'.")
        tracked_card = UserTrackedCards(
            user_id=user.id, amount=amount, card=card_entry
        )
        session.add(tracked_card)

    # We need the ID for the specifications, so we flush to get it.
    session.flush()

    # Efficiently update specifications
    if card_specs:
        # Get all existing specs for this card at once to avoid N+1 queries
        existing_specs_query = session.query(CardSpecification).filter(
            CardSpecification.user_card_id == tracked_card.id
        )
        # Load the finish relationship to avoid lazy loading in the loop
        existing_specs_query = existing_specs_query.options(
            joinedload(CardSpecification.finish),
            joinedload(CardSpecification.set))
        existing_specs_set = {
            (s.set_code, s.collector_number,
             s.finish.name if s.finish else None)
            for s in existing_specs_query.all()
        }

        for card_spec in card_specs:
            # The frontend sends a single spec object, not a list.
            if card_spec.get_key() not in existing_specs_set:
                set_obj = (
                    get_set(set_code=card_spec.set_code.code)
                    if card_spec.set_code and card_spec.set_code.code
                    else None
                )
                finish_obj = (
                    get_finish(finish_name=card_spec.finish.name)
                    if card_spec.finish and card_spec.finish.name
                    else None
                )

                new_spec = CardSpecification(
                    user_card_id=tracked_card.id,
                    set=set_obj,
                    collector_number=card_spec.collector_number,
                    finish=finish_obj,
                )
                session.add(new_spec)
                logger.info(
                    f"➕ Added new specification {card_spec.get_key()}"
                    f" for '{card_name}'."
                )

    logger.info(
        f"✅ Successfully processed '{card_name}' for user '{username}'."
    )


@db_query
def get_card(card_name: str,
             *,
             session: Session
             ) -> Optional[Card]:
    assert session is not None, "Session is injected by @db_query decorator"
    if not card_name:
        logger.error("No card name was passed in")
        return None
    card = (session.query(Card).filter(Card.name == card_name).first())
    if not card:
        logger.error("Card not found in catalogue")
        return None
    else:
        return card


@db_query
def get_tracked_card(
    username: str,
        card_name: str,
        *,
        session: Session
        ) -> Optional[UserTrackedCards]:
    assert session is not None, "Session is injected by @db_query decorator"
    user = get_user_orm_by_username(username)
    if not user:
        return None
    tracked_card = session.query(UserTrackedCards).filter(
            UserTrackedCards.user_id == user.id,
            UserTrackedCards.card_name == card_name,
        ).first()
    return tracked_card


@db_query
def search_card_names(query: str,
                      *,
                      session: Session,
                      limit: int = 10
                      ) -> List[str]:
    assert session is not None, "Session is injected by @db_query decorator"
    """
    Searches for card names in the global 'cards' table that match
    a given query. Uses a case-insensitive LIKE query for partial matching.
    """
    if not query:
        return []

    search_pattern = f"%{query}%"
    results = (
        session.query(Card.name)
        .filter(Card.name.ilike(search_pattern))
        .limit(limit)
        .all()
    )
    if len(results) == 0:
        logger.warning(f"No matching card names for query {query} found.")
        return []
    else:
        return [row[0] for row in results]


@db_query
def delete_user_card(username: str,
                     card_name: str,
                     *,
                     session: Session
                     ) -> None:
    assert session is not None, "Session is injected by @db_query decorator"
    """
    Deletes a tracked card for a user, ensuring related specifications are
      also deleted via ORM cascades.
    """
    logger.info(
        f"🗑️ Attempting to delete tracked card '{card_name}' "
        f"for user '{username}'."
    )
    user = get_user_orm_by_username(username)
    tracked_card = get_tracked_card(username, card_name)

    if not user:
        logger.warning(
            f"🚨 User '{username}' not found. Cannot delete card."
        )
    elif not tracked_card:
        logger.warning(
            f"⚠️ No tracked card named '{card_name}' found "
            f"for user '{username}'. No action taken."
        )
    else:
        session.delete(tracked_card)
        logger.info(
            f"✅ Successfully deleted tracked card '{card_name}' "
            f"for user '{username}'."
        )


@db_query
def update_user_tracked_card_preferences(
    username: str,
    card_name: str,
    preference_updates: Dict[str, Any],
    *,
    session: Session,
) -> None:
    assert session is not None, "Session is injected by @db_query decorator"
    """
    Updates specific preferences (e.g., amount) for a single tracked card.
    """
    logger.info(
        f"✏️ Updating preferences for card '{card_name}' "
        f"for user '{username}'."
    )

    # Find the specific card tracked by the user in a single query
    tracked_card = get_tracked_card(username, card_name)

    if not tracked_card:
        logger.warning(
            f"🚨 Card '{card_name}' not found for user '{username}'. "
            "Cannot update preferences."
        )
        return

    # Update preferences based on the provided dictionary
    valid_updates = (orm.UserTrackedCardUpdateSchema
                     .model_validate(preference_updates))
    if valid_updates.amount is not None:
        session.query(UserTrackedCards).filter(
            UserTrackedCards.id == tracked_card.id
        ).update({"amount": valid_updates.amount})
        logger.debug(f"Updated amount to {valid_updates.amount} "
                     f"for '{card_name}'.")

    # Handle updating specifications.
    # This replaces all existing specs for the card.
    if valid_updates.specifications is not None:
        logger.debug(f"Updating specifications for '{card_name}'.")
        # Clear existing specifications
        tracked_card.specifications.clear()
        session.flush()  # Apply the clear operation

        # Add new specifications
        for new_spec in valid_updates.specifications:
            finish_obj = get_finish(finish_name=new_spec.finish.name
                                    if new_spec.finish else None)
            set_obj = get_set(set_code=new_spec.set_code.code
                              if new_spec.set_code else None)
            card_spec = CardSpecification(
                user_card_id=tracked_card.id,
                set=set_obj,
                collector_number=new_spec.collector_number,
                finish=finish_obj,
            )
            tracked_card.specifications.append(card_spec)
            logger.debug(
                f"Added new specification for '{card_name}'.")

    logger.info(
        f"✅ Preferences updated for card '{card_name}' for user '{username}'."
    )


@db_query
def filter_existing_card_names(card_names: List[str],
                               *,
                               session: Session
                               ) -> set:
    assert session is not None, "Session is injected by @db_query decorator"
    """
    Given a list of card names, returns a set of the names that exist in the
    'cards' table.
    """
    if not card_names:
        return set()

    # Query the Card table for names that are in the provided list
    existing_names_query = session.query(Card.name).filter(
        Card.name.in_(card_names)
    )

    # Return the results as a set for efficient `in` checks.
    return {name for name, in existing_names_query}
