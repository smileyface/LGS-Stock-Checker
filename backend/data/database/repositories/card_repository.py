from typing import List, Dict, Any
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.session import Session

# Internal package imports

from schema import db
from ..session_manager import db_query
from .user_repository import get_user_orm_by_username
from ..models import (
    Card,
    CardSpecification,
    UserTrackedCards,
    Set,
    Finish,
    CardPrinting,
    printing_finish_association,
)
from utility import logger


@db_query
def get_users_cards(
    username: str,
    *,
    session: Session = Session()
) -> List[db.UserTrackedCardSchema]:
    """
    Retrieves all tracked cards for a given user using an
    efficient single query.
    """
    logger.debug(f"📖 Querying for all tracked cards for user '{username}'.")
    user = get_user_orm_by_username(username)

    if not user:
        logger.warning(f"User '{username}' not found. Cannot get cards.")
        return []

    logger.info(f"✅ Found {len(user.cards)} tracked cards for '{username}'.")
    return [
        db.UserTrackedCardSchema.model_validate(card) for card in user.cards
    ]


@db_query
def add_card_to_user(
    username: str,
    card_data: Dict[str, Any],
    *,
    session: Session = Session(),
) -> None:
    """
    Adds or updates a tracked card for a user, including its specifications.
    This function handles finding the user, finding/creating the card in the
    global card table, and then creating/updating the user-specific tracking
      information.
    """
    valid_card_data = db.UserTrackedCardSchema.model_validate(card_data)
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

    if card_entry.name is None:
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
            joinedload(CardSpecification.finish))
        existing_specs_set = {
            (s.set_code, s.collector_number,
             s.finish.name if s.finish else None)
            for s in existing_specs_query.all()
        }

        for card_spec in card_specs:
            # The frontend sends a single spec object, not a list.
            finish_name = (card_spec.finish.name
                           if card_spec.finish
                           else None)
            spec_tuple = (
                card_spec.set_code,
                card_spec.collector_number,
                finish_name,
            )
            if spec_tuple not in existing_specs_set:
                finish_obj = None
                if finish_name:
                    finish_obj = (
                        session.query(Finish).filter(Finish.name == finish_name).first()
                    )

                new_spec = CardSpecification(
                    user_card_id=tracked_card.id,
                    set_code=spec_tuple[0],
                    collector_number=spec_tuple[1],
                    finish=finish_obj,
                )
                session.add(new_spec)
                logger.info(
                    f"➕ Added new specification {spec_tuple} for '{card_name}'."
                )

    logger.info(
        f"✅ Successfully processed '{card_name}' for user '{username}'."
    )


@db_query
def get_card(card_name: str,
             *,
             session: Session = Session()) -> Card:
    if not card_name:
        logger.error("No card name was passed in")
        return Card()
    card = (session.query(Card).filter(Card.name == card_name).first())
    if not card:
        logger.error("Card not found in catalogue")
        return Card()
    else:
        return card


@db_query
def get_tracked_card(username: str,
                     card_name: str,
                     *,
                     session: Session = Session()) -> UserTrackedCards:
    user = get_user_orm_by_username(username)
    if not user:
        return UserTrackedCards()
    tracked_card = session.query(UserTrackedCards).filter(
            UserTrackedCards.user_id == user.id,
            UserTrackedCards.card_name == card_name,
        ).first()
    return tracked_card


@db_query
def search_card_names(query: str,
                      *,
                      session: Session = Session(),
                      limit: int = 10) -> List[str]:
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
        logger.warning(f"No matching card names for {Card.name} found.")
        return []
    else:
        return [row[0] for row in results]


@db_query
def delete_user_card(username: str,
                     card_name: str,
                     *,
                     session: Session = Session()) -> None:
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
    session: Session = Session(),
) -> None:
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
    valid_updates = db.UserTrackedCardUpdateSchema.model_validate(preference_updates)
    if valid_updates.amount is not None:
        session.query(UserTrackedCards).filter(
            UserTrackedCards.id == tracked_card.id
        ).update({"amount": valid_updates.amount})
        logger.debug(f"Updated amount to {valid_updates.amount} for '{card_name}'.")

    # Handle updating specifications.
    # This replaces all existing specs for the card.
    if valid_updates.specifications is not None:
        logger.debug(f"Updating specifications for '{card_name}'.")
        # Clear existing specifications
        tracked_card.specifications.clear()
        session.flush()  # Apply the clear operation

        # Add new specifications
        for new_spec in valid_updates.specifications:
            finish_obj = None
            if new_spec.finish and new_spec.finish.name:
                finish_obj = (
                    session.query(Finish)
                    .filter(Finish.name == new_spec.finish.name)
                    .first()
                )
            card_spec = CardSpecification(
                user_card_id=tracked_card.id,
                set_code=new_spec.set_code,
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
def add_card_names_to_catalog(card_names: List[str], *, session):
    """
    Adds a list of card names to the cards table, ignoring any duplicates.
    This uses a PostgreSQL-specific "INSERT ... ON CONFLICT DO NOTHING" for
    high performance.

    Args:
        session: The SQLAlchemy session.
        card_names: A list of card names to add.
    """
    if not card_names:
        logger.info("No new card names provided to add to catalog. Skipping.")
        return

    # Prepare the data for bulk insert. Each item is a dictionary.
    stmt = insert(Card).values([{"name": name} for name in card_names])

    # Use on_conflict_do_nothing to ignore duplicates based on the primary key
    # ('name') This compiles to `INSERT OR IGNORE` on SQLite and is compatible
    # with PostgreSQL's `ON CONFLICT DO NOTHING` when the conflict target is
    # the primary key.
    stmt = stmt.on_conflict_do_nothing()

    session.execute(stmt)
    logger.info(
        f"Attempted to bulk insert {len(card_names)} names "
        f"into the card catalog."
    )


@db_query
def add_set_data_to_catalog(set_data: List[Dict[str, Any]], *, session):
    """
    Adds a list of set data to the sets table, ignoring any duplicates.

    Args:
        session: The SQLAlchemy session.
        set_data: A list of set data dictionaries to add.
    """
    if not set_data:
        logger.info("No new set data provided to add to catalog. Skipping.")
        return

    # Prepare the data for bulk insert.
    stmt = insert(Set).values(set_data)

    # Use a dialect-agnostic `on_conflict_do_nothing` for compatibility.
    stmt = stmt.on_conflict_do_nothing()

    session.execute(stmt)
    logger.info(
        f"Attempted to bulk insert {len(set_data)} sets into the set catalog."
    )


@db_query
def is_card_in_catalog(card_name: str, *, session) -> bool:
    """Checks if a card with the given name exists in the catalog."""
    # The correct way to check for existence is to create an exists()
    # subquery and then query for its scalar result.
    exists_query = (
        session.query(Card.name).filter(Card.name == card_name).exists()
    )
    return session.query(exists_query).scalar()


@db_query
def filter_existing_card_names(card_names: List[str], *, session) -> set:
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


@db_query
def bulk_add_finishes(finish_names: List[str], *, session):
    if not finish_names:
        return
    stmt = insert(Finish).values([{"name": name} for name in finish_names])
    stmt = stmt.on_conflict_do_nothing()
    session.execute(stmt)
    logger.info(f"Attempted to bulk insert {len(finish_names)} finishes.")


@db_query
def bulk_add_card_printings(printings: List[Dict[str, Any]], *, session):
    if not printings:
        return
    stmt = insert(CardPrinting).values(printings)
    stmt = stmt.on_conflict_do_nothing()
    session.execute(stmt)
    logger.info(f"Attempted to bulk insert {len(printings)} card printings.")


@db_query
def get_all_printings_map(*, session) -> Dict[tuple, int]:
    results = session.query(
        CardPrinting.id,
        CardPrinting.card_name,
        CardPrinting.set_code,
        CardPrinting.collector_number,
    ).all()
    return {
        (r.card_name, r.set_code, r.collector_number): r.id for r in results
    }


@db_query
def get_all_finishes_map(*, session) -> Dict[str, int]:
    results = session.query(Finish.id, Finish.name).all()
    return {r.name: r.id for r in results}


@db_query
def bulk_add_printing_finish_associations(
    associations: List[Dict[str, int]], *, session
):
    """
    Bulk inserts printing-to-finish associations.
    Uses a dialect-specific approach for conflict handling to support both
    PostgreSQL and SQLite (for testing).
    """
    if not associations:
        return

    stmt = insert(printing_finish_association).values(associations)

    # The `on_conflict_do_nothing()` method is compatible with both PostgreSQL
    # and modern versions of SQLite, where it compiles to `INSERT OR IGNORE`.
    # This handles cases where an association might already exist.
    stmt = stmt.on_conflict_do_nothing()

    session.execute(stmt)
    logger.info(
        f"Attempted to bulk insert {len(associations)} printing-finish "
        f"associations."
    )


@db_query
def get_printings_for_card(card_name: str,
                           *,
                           session: Session = Session()) -> List[Dict[str, Any]]:
    """
    Retrieves all printings for a given card name, including their available
    finishes.
    This is used to populate the UI with valid specification options.
    Implements requirement [4.3.5].
    """
    logger.debug(f"📖 Querying for all printings of card '{card_name}'.")
    printings = (
        session.query(CardPrinting)
        .filter(CardPrinting.card_name == card_name)
        .options(
            joinedload(CardPrinting.available_finishes)
        )  # Eagerly load finishes
        .order_by(CardPrinting.set_code, CardPrinting.collector_number)
        .all()
    )

    if not printings:
        return []

    return [
        {
            "set_code": p.set_code,
            "collector_number": p.collector_number,
            "finishes": [f.name for f in p.available_finishes],
        }
        for p in printings
    ]


@db_query
def is_valid_printing_specification(
    card_name: str,
    spec: Dict[str, Any],
    *,
    session: Session = Session()
) -> bool:
    """
    Validates if a given specification (set, collector #, finish) is valid for
    a card.
    Handles partial specifications as wildcards, as per requirement [4.3.8].

    Args:
        card_name: The name of the card.
        spec: A dictionary with 'set_code', 'collector_number', and 'finish'.

    Returns:
        True if the specification is valid, False otherwise.
    """

    logger.info(f"🔍 Validating specification for '{card_name}': {spec}")
    # Create a cleaned specification, ignoring any keys with empty string
    # values.
    # This treats them as wildcards, as intended.
    cleaned_spec = {key: value for key, value in spec.items() if value}

    # If the cleaned spec is empty, it's a wildcard for any printing,
    # which is always valid.
    if not cleaned_spec:
        logger.debug(
            f"Validation passed for '{card_name}' with empty spec (wildcard)."
        )
        return True

    # Start a query on CardPrinting
    query = session.query(CardPrinting).filter(
        CardPrinting.card_name == card_name
    )

    # Add filters for the specs that are actually provided in the cleaned
    # dictionary
    if "set_code" in cleaned_spec:
        query = query.filter(CardPrinting.set_code == cleaned_spec["set_code"])
    if "collector_number" in cleaned_spec:
        query = query.filter(
            CardPrinting.collector_number == cleaned_spec["collector_number"]
        )
    if "finish" in cleaned_spec:
        # If a finish is specified, we must join to check it
        query = query.join(CardPrinting.available_finishes).filter(
            Finish.name == cleaned_spec["finish"]
        )

    # We just need to know if at least one such printing exists.
    # The .scalar() method returns the first column of the first row, or None.
    exists = session.query(query.exists()).scalar()

    if not exists:
        logger.warning(f"Validation failed for '{card_name}' "
                       f"with spec: {spec}")

    return exists
