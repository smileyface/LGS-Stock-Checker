from typing import List, Dict, Any, Optional

from utility import logger
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, joinedload

from ..session_manager import db_query
from ..models import (
    Card,
    Finish,
    CardPrinting,
    Set,
    printing_finish_association,
)


@db_query
def add_card_names_to_catalog(card_names: List[str],
                              *,
                              session: Session = Session()) -> None:
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
def add_set_data_to_catalog(set_data: List[Dict[str, Any]],
                            *,
                            session: Session = Session()) -> None:
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
def is_card_in_catalog(card_name: str,
                       *,
                       session: Session = Session()) -> bool:
    """Checks if a card with the given name exists in the catalog."""
    # The correct way to check for existence is to create an exists()
    # subquery and then query for its scalar result.
    exists_query = (
        session.query(Card.name)
        .filter(Card.name == card_name)
        .exists()
    )
    return session.query(exists_query).scalar()


@db_query
def bulk_add_finishes(finish_names: List[str],
                      *,
                      session: Session = Session()) -> None:
    if not finish_names:
        return
    stmt = insert(Finish).values([{"name": name} for name in finish_names])
    stmt = stmt.on_conflict_do_nothing()
    session.execute(stmt)
    logger.info(f"Attempted to bulk insert {len(finish_names)} finishes.")


@db_query
def bulk_add_card_printings(printings: List[Dict[str, Any]],
                            *,
                            session: Session = Session()) -> None:
    if not printings:
        return
    stmt = insert(CardPrinting).values(printings)
    stmt = stmt.on_conflict_do_nothing()
    session.execute(stmt)
    logger.info(f"Attempted to bulk insert {len(printings)} card printings.")


@db_query
def get_all_printings_map(*,
                          session: Session = Session()) -> Dict[tuple, int]:
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
def get_all_finishes_map(*,
                         session: Session = Session()) -> Dict[str, int]:
    results = session.query(Finish.id, Finish.name).all()
    return {r.name: r.id for r in results}


@db_query
def bulk_add_printing_finish_associations(
    associations: List[Dict[str, int]],
    *,
    session: Session = Session()
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
                           session: Session = Session()) -> List[
                               Dict[str, Any]]:
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


@db_query
def get_set(set_name: Optional[str] = None,
            set_code: Optional[str] = None,
            *,
            session: Session = Session()) -> Optional[Set]:
    set_listing = None
    if not set_name and not set_code:
        logger.error("Neither set_name nor set_code provided. Aborting.")
    elif set_name:
        set_listing = session.query(Set).filter(Set.name == set_name).first()
        if set_listing is None:
            logger.error("Set not found in catalog. Aborting.")
    else:
        set_listing = session.query(Set).filter(Set.code == set_code).first()
        if set_listing is None:
            logger.error("Set not found in catalog. Aborting.")
    return set_listing


@db_query
def get_finish(finish_name: Optional[str] = None,
               *,
               session: Session = Session()) -> Optional[Finish]:
    if not finish_name:
        logger.error("No finish name provided. Aborting.")
        return None
    return session.query(Finish).filter(Finish.name == finish_name).first()
