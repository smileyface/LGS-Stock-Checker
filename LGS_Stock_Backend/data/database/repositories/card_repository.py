from typing import List, Dict, Any
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import joinedload

# Internal package imports

from .. import schema
from ..exceptions import InvalidSpecificationError
from ..session_manager import db_query
from ..models import Card, CardSpecification, User, UserTrackedCards, Set, Finish, CardPrinting, printing_finish_association
from utility import logger

@db_query
def get_users_cards(username: str, *, session) -> List[schema.UserTrackedCardSchema]:
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
def add_user_card(username: str, card_name: str, amount: int, card_specs: Dict[str, Any], *, session) -> None:
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
        logger.info(f"🔄 User '{username}' is already tracking '{card_name}'. Adding new specifications if any.")
        # Amount is not updated here; use `update_user_tracked_card_preferences` for that.
    else:
        logger.info(f"➕ User '{username}' is now tracking '{card_name}'.")
        tracked_card = UserTrackedCards(user_id=user.id, amount=amount, card_name=card_name)
        session.add(tracked_card)

    # Validate specifications before adding them
    if card_specs and not is_valid_printing_specification(card_name, card_specs):
        # Raise a specific exception that can be caught by the caller
        raise InvalidSpecificationError(
            f"Invalid specification for '{card_name}': {card_specs}"
        )

    # We need the ID for the specifications, so we flush to get it.
    session.flush()

    # Efficiently update specifications
    if card_specs:
        # Get all existing specs for this card at once to avoid N+1 queries
        existing_specs_query = session.query(CardSpecification).filter(CardSpecification.user_card_id == tracked_card.id)
        existing_specs_set = {
            (s.set_code, s.collector_number, s.finish) for s in existing_specs_query.all()
        }

        # The frontend sends a single spec object, not a list.
        spec_tuple = (
            card_specs.get("set_code"),
            card_specs.get("collector_number"),
            card_specs.get("finish")
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
def search_card_names(query: str, *, session, limit: int = 10) -> List[str]:
    """
    Searches for card names in the global 'cards' table that match a given query.
    Uses a case-insensitive LIKE query for partial matching.
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
    # The result is a list of tuples, e.g., [('Lightning Bolt',)], so we extract the first element.
    return [row[0] for row in results]


@db_query
def delete_user_card(username: str, card_name: str, *, session) -> None:
    """
    Deletes a tracked card for a user, ensuring related specifications are also deleted via ORM cascades.
    """
    logger.info(f"🗑️ Attempting to delete tracked card '{card_name}' for user '{username}'.")

    # Find the specific card tracked by the user.
    # We must load the object into the session to trigger cascade deletes for its specifications.
    # A bulk delete (`.delete()`) bypasses this ORM-level logic.
    tracked_card = (
        session.query(UserTrackedCards)
        .join(User)
        .filter(User.username == username, UserTrackedCards.card_name == card_name)
        .first()
    )

    if tracked_card:
        session.delete(tracked_card)
        logger.info(f"✅ Successfully deleted tracked card '{card_name}' for user '{username}'.")
    else:
        # This could be because the user doesn't exist or they aren't tracking the card.
        logger.warning(f"⚠️ No tracked card named '{card_name}' found for user '{username}'. No action taken.")


@db_query
def update_user_tracked_cards_list(username: str, card_list: List[Dict[str, Any]], *, session) -> None:
    """
    Replaces a user's entire tracked card list with a new one.
    This uses an idiomatic "set" operation, letting the ORM handle deletes and inserts.
    """
    logger.info(f"🔄 Replacing entire tracked card list for user '{username}'.")
    user = session.query(User).options(joinedload(User.cards)).filter(User.username == username).first()
    if not user:
        logger.warning(f"🚨 User '{username}' not found. Cannot update card list.")
        return

    # By assigning a new list to the 'cards' relationship, SQLAlchemy's ORM
    # will handle the cascade delete for the old UserTrackedCards and their associated
    # CardSpecification records, respecting foreign key constraints.

    if not card_list:
        user.cards = []
        logger.info(f"✅ Cleared all card preferences for user '{username}' as the provided list was empty.")
        return

    # Create new card preference objects
    new_tracked_cards = []
    for card_data in card_list:
        # Note: This assumes card_name is valid and doesn't re-verify against the `cards` table
        # for performance. The `add_user_card` flow is better for single additions.
        new_tracked_cards.append(
            UserTrackedCards(
                # user_id is set via the relationship back-reference
                card_name=card_data["card_name"],
                amount=card_data.get("amount", 1)
            )
        )

    user.cards = new_tracked_cards
    logger.info(f"✅ Successfully set {len(card_list)} new tracked cards for user '{username}'.")


@db_query
def update_user_tracked_card_preferences(username: str, card_name: str, preference_updates: Dict[str, Any], *, session) -> None:
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

    # Handle updating specifications. This replaces all existing specs for the card.
    if "specifications" in preference_updates:
        logger.debug(f"Updating specifications for '{card_name}'.")
        # Clear existing specifications
        tracked_card.specifications.clear()
        session.flush() # Apply the clear operation

        # Add new specifications
        new_specs = preference_updates["specifications"]
        for spec_data in new_specs:
            new_spec = CardSpecification(
                set_code=spec_data.get("set_code"),
                collector_number=spec_data.get("collector_number"),
                finish=spec_data.get("finish")
            )
            tracked_card.specifications.append(new_spec)
        logger.debug(f"Added {len(new_specs)} new specifications for '{card_name}'.")

    logger.info(f"✅ Preferences updated for card '{card_name}' for user '{username}'.")

@db_query
def add_card_names_to_catalog(card_names: List[str], *, session):
    """
    Adds a list of card names to the cards table, ignoring any duplicates.
    This uses a PostgreSQL-specific "INSERT ... ON CONFLICT DO NOTHING" for high performance.

    Args:
        session: The SQLAlchemy session.
        card_names: A list of card names to add.
    """
    if not card_names:
        logger.info("No new card names provided to add to catalog. Skipping.")
        return

    # Prepare the data for bulk insert. Each item is a dictionary.
    stmt = insert(Card).values([{"name": name} for name in card_names])

    # Use on_conflict_do_nothing to ignore duplicates based on the primary key ('name')
    # This compiles to `INSERT OR IGNORE` on SQLite and is compatible with PostgreSQL's
    # `ON CONFLICT DO NOTHING` when the conflict target is the primary key.
    stmt = stmt.on_conflict_do_nothing()

    session.execute(stmt)
    logger.info(f"Attempted to bulk insert {len(card_names)} names into the card catalog.")

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
    logger.info(f"Attempted to bulk insert {len(set_data)} sets into the set catalog.")

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
    results = session.query(CardPrinting.id, CardPrinting.card_name, CardPrinting.set_code, CardPrinting.collector_number).all()
    return {(r.card_name, r.set_code, r.collector_number): r.id for r in results}

@db_query
def get_all_finishes_map(*, session) -> Dict[str, int]:
    results = session.query(Finish.id, Finish.name).all()
    return {r.name: r.id for r in results}

@db_query
def bulk_add_printing_finish_associations(associations: List[Dict[str, int]], *, session):
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
    logger.info(f"Attempted to bulk insert {len(associations)} printing-finish associations.")

@db_query
def get_printings_for_card(card_name: str, *, session) -> List[Dict[str, Any]]:
    """
    Retrieves all printings for a given card name, including their available finishes.
    This is used to populate the UI with valid specification options.
    Implements requirement [4.3.5].
    """
    logger.debug(f"📖 Querying for all printings of card '{card_name}'.")
    printings = (
        session.query(CardPrinting)
        .filter(CardPrinting.card_name == card_name)
        .options(joinedload(CardPrinting.available_finishes))  # Eagerly load finishes
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
def is_valid_printing_specification(card_name: str, spec: Dict[str, Any], *, session) -> bool:
    """
    Validates if a given specification (set, collector #, finish) is valid for a card.
    Handles partial specifications as wildcards, as per requirement [4.3.8].

    Args:
        card_name: The name of the card.
        spec: A dictionary with 'set_code', 'collector_number', and 'finish'.

    Returns:
        True if the specification is valid, False otherwise.
    """
    set_code = spec.get("set_code")
    collector_number = spec.get("collector_number")
    finish = spec.get("finish")

    # If no specs are provided at all, it's trivially valid (wildcard for everything).
    if not set_code and not collector_number and not finish:
        return True

    # Start a query on CardPrinting
    query = session.query(CardPrinting).filter(CardPrinting.card_name == card_name)

    # Add filters for the specs that are actually provided
    if set_code:
        query = query.filter(CardPrinting.set_code == set_code)
    if collector_number:
        query = query.filter(CardPrinting.collector_number == collector_number)
    if finish:
        # If a finish is specified, we must join to check it
        query = query.join(CardPrinting.available_finishes).filter(Finish.name == finish)

    # We just need to know if at least one such printing exists.
    exists = session.query(query.exists()).scalar()

    if not exists:
        logger.warning(f"Validation failed for '{card_name}' with spec: {spec}")

    return exists
