"""
User repository functions for managing user data and preferences in
the database.

Includes operations to fetch user details, add new users, update usernames
and passwords, retrieve selected stores, and manage user store preferences.
Utilizes internal schema models and database session management patterns.
"""

from typing import List, Optional
from sqlalchemy.orm import joinedload, Session

# Internal package imports (relative to the data.database package)
from .. import schema
from ..session_manager import db_query
from ..models.orm_models import (
    User,
    UserTrackedCards,
    Store,
)

# Project package imports
from utility import logger


@db_query
def get_user_by_username(
    username: str, session: Session = None
) -> Optional[schema.UserDBSchema]:
    # This assert tells Pylance that session is not None
    assert session is not None, "Session is injected by @db_query decorator"
    """
    Retrieve a user by username from the database, including sensitive fields,
    and return as a UserDBSchema instance.

    Args:
        username (str): The unique username of the user to fetch.
        session (Session, optional): The database session to use.
            Defaults to None.

    Returns:
        UserDBSchema or None: The user data as a UserDBSchema if found,
        otherwise None.
    """

    logger.debug(f"📖 Querying for user '{username}' with full DB schema.")
    # Eagerly load the 'selected_stores' relationship to ensure the Pydantic
    # schema can be created without causing a DetachedInstanceError.
    user_orm = (
        session.query(User)
        .options(joinedload(User.selected_stores))
        .filter(User.username == username)
        .first()
    )
    if user_orm:
        logger.debug(f"✅ Found user '{username}'.")
        # Use UserDBSchema.model_validate to convert the ORM object
        return schema.UserDBSchema.model_validate(user_orm)

    logger.debug(f"❌ User '{username}' not found in database.")
    return None


@db_query
def get_user_orm_by_username(username: str,
                             session: Session = None) -> Optional[User]:
    # This assert tells Pylance that session is not None
    assert session is not None, "Session is injected by @db_query decorator"
    """
    Retrieve a user ORM object by username from the database.
    This is intended for internal use where the ORM object's methods are
    needed (e.g., authentication).

    Args:
        username (str): The unique username of the user to fetch.

    Returns:
        User or None: The SQLAlchemy User ORM object if found, otherwise None.
    """
    logger.debug(f"📖 Querying for user ORM object '{username}'.")
    user_orm = session.query(User).filter(User.username == username).first()
    logger.debug(
        f"✅ Found user ORM object for '{username}'."
        if user_orm
        else f"❌ User ORM object for '{username}' not found."
    )
    return user_orm


@db_query
def get_user_orm_by_id(user_id: int,
                       session: Session = None) -> Optional[User]:
    # This assert tells Pylance that session is not None
    assert session is not None, "Session is injected by @db_query decorator"
    """
    Retrieve a user ORM object by its primary key ID.
    This is used by Flask-Login's user_loader.

    Args:
        user_id (int): The primary key ID of the user.

    Returns:
        User or None: The SQLAlchemy User ORM object if found, otherwise None.
    """
    logger.debug(f"📖 Querying for user ORM object with ID '{user_id}'.")
    # Use joinedload to eagerly fetch the selected_stores relationship.
    # This prevents a DetachedInstanceError when current_user.to_dict()
    # is called later, as the stores will already be loaded and won't
    # require a lazy load.
    user_orm = (
        session.query(User)
        .options(joinedload(User.selected_stores))
        .filter(User.id == user_id)
        .first()
    )
    logger.debug(
        f"✅ Found user ORM object for ID '{user_id}'."
        if user_orm
        else f"❌ User ORM object for ID '{user_id}' not found."
    )
    return user_orm


@db_query
def add_user(
    username: str, password_hash: str, session: Session = None
) -> Optional[schema.UserPublicSchema]:
    # This assert tells Pylance that session is not None
    assert session is not None, "Session is injected by @db_query decorator"
    """
    Add a new user to the database with the given username and password hash.

    Args:
        username (str): The username for the new user.
        password_hash (str): The hashed password for the new user.

    Returns:
        UserPublicSchema or None: The newly created user's public data, or
        None on failure.

    Logs:
        Success or failure of the user addition operation.
    """
    logger.info(f"➕ Adding user '{username}' to the database.")
    new_user = User(username=username, password_hash=password_hash)
    session.add(new_user)
    # Flush to assign an ID and ensure the object is persisted before the
    # session closes.
    session.flush()
    logger.info(f"✅ User {username} added to the database")
    return schema.UserPublicSchema.model_validate(new_user)


@db_query
def update_username(old_username: str, new_username: str,
                    session: Session = None) -> None:
    # This assert tells Pylance that session is not None
    assert session is not None, "Session is injected by @db_query decorator"
    """
    Update a user's username in the database.

    Args:
        old_username (str): The current username of the user.
        new_username (str): The new username to assign.

    Returns:
        None: None if the operation was successful, otherwise raises an
        exception.

    Logs:
        Success or failure of the username update operation.
    """
    logger.info(
        f"✏️ Updating username from '{old_username}' to '{new_username}'."
    )
    user = session.query(User).filter(User.username == old_username).first()
    if not user:
        logger.warning(
            f"🚨 User '{old_username}' not found. Cannot update username."
        )
        return
    user.username = new_username
    logger.info(
        f"✅ Username updated successfully: {old_username} → {new_username}"
    )


@db_query
def update_password(username: str,
                    password_hash: str,
                    session: Session = None) -> None:
    # This assert tells Pylance that session is not None
    assert session is not None, "Session is injected by @db_query decorator"
    """
    Update the password hash for a user identified by username.

    Args:
        username (str): The username of the user whose password is to be
        updated.
        password_hash (str): The new hashed password.

    Returns:
        None: None if the operation was successful, otherwise raises an
        exception.

    Logs:
        Success or failure of the password update operation.
    """
    logger.info(f"🔑 Updating password for user '{username}'.")
    user = session.query(User).filter(User.username == username).first()
    if not user:
        logger.warning(
            f"🚨 User '{username}' not found. Cannot update password."
        )
        return
    user.password_hash = password_hash
    logger.info(f"✅ Password for {username} updated successfully!")


@db_query
def get_user_stores(username: str,
                    session: Session = None) -> List[schema.StoreSchema]:
    # This assert tells Pylance that session is not None
    assert session is not None, "Session is injected by @db_query decorator"
    """
    Fetches the list of stores selected by the specified user.

    Args:
        username (str): The username of the user.

    Returns:
        List[schema.StoreSchema]: A list of StoreSchema objects representing
        the user's selected stores.

    Logs:
        Success or failure of the store retrieval operation.
    """
    logger.debug(f"🛍️ Fetching selected stores for user '{username}'.")
    user = (
        session.query(User)
        .options(joinedload(User.selected_stores))
        .filter(User.username == username)
        .first()
    )
    if not user:
        logger.warning(
            f"🚨 User '{username}' not found. Cannot retrieve stores."
        )
        return []
    # Convert ORM objects to DTOs before returning
    logger.debug(
        f"✅ Found {len(user.selected_stores)} stores for user '{username}'."
    )
    return [
        schema.StoreSchema.model_validate(store_orm)
        for store_orm in user.selected_stores
    ]


@db_query
def add_user_store(username: str,
                   store_slug: str,
                   session: Session = None) -> None:
    # This assert tells Pylance that session is not None
    assert session is not None, "Session is injected by @db_query decorator"
    """
    Adds a store to the user's selected stores using an idiomatic ORM approach.

    Args:
        username (str): The username of the user.
        store_slug (str): The slug of the store to add.

    Logs:
        Success or failure of the store addition operation.
    """
    # Use joinedload to fetch the user and their selected stores in one query
    user = (
        session.query(User)
        .options(joinedload(User.selected_stores))
        .filter(User.username == username)
        .first()
    )
    if not user:
        logger.warning(
            f"User '{username}' not found. Cannot add store preference."
        )
        return

    # Check if the store is already in the user's preferences to prevent
    #  duplicates
    if any(s.slug == store_slug for s in user.selected_stores):
        logger.info(
            f"User '{username}' already has store '{store_slug}'."
        )
        return

    store_obj = session.query(Store).filter(Store.slug == store_slug).first()
    if not store_obj:
        logger.warning(
            f"Store with slug '{store_slug}' not found. "
            f"Cannot add store preference."
        )
        return

    # Add the store to the user's preferences
    user.selected_stores.append(store_obj)
    logger.info(f"✅ Added '{store_slug}' to user '{username}' preferences.")


@db_query
def remove_user_store(username: str, store_slug: str,
                      session: Session = None) -> None:
    # This assert tells Pylance that session is not None
    assert session is not None, "Session is injected by @db_query decorator"
    """
    Removes a store from the user's selected stores.

    Args:
        username (str): The username of the user.
        store_slug (str): The slug of the store to remove.

    Logs:
        Success or failure of the store removal operation.
    """
    user = (
        session.query(User)
        .options(joinedload(User.selected_stores))
        .filter(User.username == username)
        .first()
    )
    if not user:
        logger.warning(
            f"User '{username}' not found. Cannot remove store preference."
        )
        return

    # Find the specific store object in the user's collection to remove it
    store_to_remove = next(
        (s for s in user.selected_stores if s.slug == store_slug), None
    )

    if store_to_remove:
        user.selected_stores.remove(store_to_remove)
        logger.info(
            f"✅ Removed '{store_slug}' from user '{username}' preferences."
        )
    else:
        logger.warning(
            f"User '{username}' does not have preference for "
            f"store '{store_slug}'. Cannot remove."
        )


@db_query
def set_user_stores(username: str, store_slugs: List[str],
                    session: Session = None) -> None:
    # This assert tells Pylance that session is not None
    assert session is not None, "Session is injected by @db_query decorator"
    """
    Sets the user's selected stores to the exact list provided,
    adding new ones and removing old ones.
    """
    user = (
        session.query(User)
        .options(joinedload(User.selected_stores))
        .filter(User.username == username)
        .first()
    )
    if not user:
        logger.warning(
            f"User '{username}' not found. Cannot set store preferences."
        )
        return

    # Fetch all valid store objects from the database that
    # are in the provided list.
    # This prevents trying to add stores that don't exist.
    if store_slugs:
        valid_stores = (
            session.query(Store).filter(Store.slug.in_(store_slugs)).all()
        )
    else:
        valid_stores = []
        logger.info(
            f"Empty store list provided for user '{username}'. "
            "All store preferences will be cleared."
        )

    # The user's selected_stores relationship will now point to this new list.
    # SQLAlchemy's ORM is smart enough to figure out which entries to add and
    # remove from the user_store_preferences association table.
    user.selected_stores = valid_stores

    logger.info(
        f"✅ Set preferred stores for user '{username}' "
        f"to: {[s.slug for s in valid_stores]}"
    )


@db_query
def get_user_for_display(
    username: str, session: Session = None
) -> Optional[schema.UserPublicSchema]:
    # This assert tells Pylance that session is not None
    assert session is not None, "Session is injected by @db_query decorator"
    """
    Retrieve a user by username from the database, excluding sensitive fields,
      and return as a UserPublicSchema instance.

    Args:
        username (str): The unique username of the user to fetch.

    Returns:
        UserPublicSchema or None: The user data as a UserPublicSchema
            if found, otherwise None.

    Logs:
        Success or failure of the user retrieval operation.
    """
    # Eagerly load the 'selected_stores' relationship to ensure the Pydantic
    # schema can be created without causing a DetachedInstanceError.
    user_orm = (
        session.query(User)
        .options(joinedload(User.selected_stores))
        .filter(User.username == username)
        .first()
    )
    if user_orm:
        logger.info(f"✅ User '{username}' retrieved successfully.")
        return schema.UserPublicSchema.model_validate(user_orm)
    logger.warning(f"❌ User '{username}' not found.")
    return None


@db_query
def get_all_users(session: Session = None) -> List[schema.UserPublicSchema]:
    # This assert tells Pylance that session is not None
    assert session is not None, "Session is injected by @db_query decorator"
    """
    Retrieve all users from the database, excluding sensitive fields.

    Returns:
        List[UserPublicSchema]: A list of all users as
            UserPublicSchema instances.
    """
    logger.debug("📖 Querying for all users.")
    users_orm = (
        session.query(User).options(joinedload(User.selected_stores)).all()
    )
    logger.info(f"✅ Retrieved {len(users_orm)} users from the database.")
    return [schema.UserPublicSchema.model_validate(user) for user in users_orm]


@db_query
def get_users_tracking_card(
    card_name: str, session: Session = None
) -> list[schema.UserPublicSchema]:
    # This assert tells Pylance that session is not None
    assert session is not None, "Session is injected by @db_query decorator"
    """
    Finds all users who are tracking a specific card.

    Args:
        card_name (str): The name of the card to search for.

    Returns:
        list[schema.UserPublicSchema]:
            A list of User objects who are tracking the specified card.
    """
    logger.debug(f"📖 Querying for users tracking card '{card_name}'.")
    users_orm = (
        session.query(User)
        .options(joinedload(User.selected_stores))
        .join(User.cards)
        .filter(UserTrackedCards.card_name == card_name)
        .all()
    )
    logger.debug(f"✅ Found {len(users_orm)} users tracking '{card_name}'.")
    return [schema.UserPublicSchema.model_validate(user) for user in users_orm]


@db_query
def get_tracking_users_for_cards(
    card_names: list[str], session: Session = None
) -> dict[str, list[schema.UserPublicSchema]]:
    # This assert tells Pylance that session is not None
    assert session is not None, "Session is injected by @db_query decorator"
    """
    Efficiently finds all users tracking any of the given card names.

    Args:
        card_names (list[str]): A list of card names to check.

    Returns:
        dict[str, list[schema.UserPublicSchema]]: A dictionary mapping
            each card name to a list of User schemas.
    """
    if not card_names:
        return {}

    logger.debug(
        f"📖 Querying for users tracking {len(card_names)} different cards."
    )
    tracked_cards_with_users = (
        session.query(UserTrackedCards)
        .filter(UserTrackedCards.card_name.in_(card_names))
        .options(
            joinedload(UserTrackedCards.user).joinedload(User.selected_stores)
        )
        .all()
    )

    card_to_users_map = {name: [] for name in card_names}
    for tracked_card in tracked_cards_with_users:
        if tracked_card.user:
            user_schema = schema.UserPublicSchema.model_validate(
                tracked_card.user
            )
            card_to_users_map[tracked_card.card_name].append(user_schema)

    logger.debug("✅ Finished mapping cards to tracking users.")
    return card_to_users_map
