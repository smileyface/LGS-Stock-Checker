"""
User repository functions for managing user data and preferences in the database.

Includes operations to fetch user details, add new users, update usernames and passwords,
retrieve selected stores, and manage user store preferences. Utilizes internal schema
models and database session management patterns.
"""
from typing import List, Optional

from data.database import schema
from data.database.session_manager import db_query
from data.database.models.orm_models import User, UserTrackedCards, Store, user_store_preferences
from utility.logger import logger

from sqlalchemy.orm import joinedload

@db_query
def get_user_by_username(username: str, session) -> Optional[schema.UserDBSchema]:
    """
    Retrieve a user by username from the database, including sensitive fields, and return as a UserDBSchema instance.

    Args:
        username (str): The unique username of the user to fetch.
        session: The database session, injected by the db_query decorator.

    Returns:
        UserDBSchema or None: The user data as a UserDBSchema if found, otherwise None.
    """
    user_orm = session.query(User).where(User.username == username).first()
    if user_orm:
        # Use UserDBSchema.model_validate to convert the ORM object
        return schema.UserDBSchema.model_validate(user_orm)
    return None


@db_query
def add_user(username: str, password_hash: str, session) -> Optional[schema.UserPublicSchema]:
    """
    Add a new user to the database with the given username and password hash.

    Args:
        username (str): The username for the new user.
        password_hash (str): The hashed password for the new user.
        session: The database session (injected by the db_query decorator).

    Returns:
        UserPublicSchema or None: The newly created user's public data, or None on failure.

    Logs:
        Success or failure of the user addition operation.
    """
    new_user = User(username=username, password_hash=password_hash)
    session.add(new_user)
    session.flush()  # Flush to assign an ID and ensure the object is persisted before the session closes.
    logger.info(f"✅ User {username} added to the database")
    return schema.UserPublicSchema.model_validate(new_user)


@db_query
def update_username(old_username: str, new_username: str, session):
    """
    Update a user's username in the database.

    Args:
        old_username (str): The current username of the user.
        new_username (str): The new username to assign.
        session: The database session (injected by the db_query decorator).

    Returns:
        None: None if the operation was successful, otherwise raises an exception.

    Logs:
        Success or failure of the username update operation.
    """
    user = session.query(User).where(User.username == old_username).first()
    if not user:
        logger.warning(f"🚨 User '{old_username}' not found. Cannot update username.")
        return
    user.username = new_username
    logger.info(f"✅ Username updated successfully: {old_username} → {new_username}")


@db_query
def update_password(username, password_hash, session):
    """
    Update the password hash for a user identified by username.

    Args:
        username (str): The username of the user whose password is to be updated.
        password_hash (str): The new hashed password.
        session: The database session (injected by the db_query decorator).

    Returns:
        None: None if the operation was successful, otherwise raises an exception.

    Logs:
        Success or failure of the password update operation.
    """
    user = session.query(User).where(User.username == username).first()
    if not user:
        logger.warning(f"🚨 User '{username}' not found. Cannot update password.")
        return
    user.password_hash = password_hash
    logger.info(f"✅ Password for {username} updated successfully!")


@db_query
def get_user_stores(username: str, session) -> List[schema.StoreSchema]:
    """
    Fetches the list of stores selected by the specified user.

    Args:
        username (str): The username of the user.
        session: The database session (injected by the db_query decorator).

    Returns:
        List[schema.StoreSchema]: A list of StoreSchema objects representing the user's selected stores.

    Logs:
        Success or failure of the store retrieval operation.
    """
    user = session.query(User).where(User.username == username).first()
    if not user:
        return []
    # Convert ORM objects to DTOs before returning
    return [schema.StoreSchema.model_validate(store_orm) for store_orm in user.selected_stores]


@db_query
def add_user_store(username: str, store_slug: str, session) -> None:
    """
    Adds a store to the user's selected stores using an idiomatic ORM approach.

    Args:
        username (str): The username of the user.
        store_slug (str): The slug of the store to add.
        session (Session): The database session (injected by the db_query decorator).

    Logs:
        Success or failure of the store addition operation.
    """
    # Use joinedload to fetch the user and their selected stores in one query
    user = session.query(User).options(joinedload(User.selected_stores)).filter(User.username == username).first()
    if not user:
        logger.warning(f"User '{username}' not found. Cannot add store preference.")
        return

    # Check if the store is already in the user's preferences to prevent duplicates
    if any(s.slug == store_slug for s in user.selected_stores):
        logger.info(f"User '{username}' already has preference for store '{store_slug}'.")
        return

    store_obj = session.query(Store).filter(Store.slug == store_slug).first()
    if not store_obj:
        logger.warning(f"Store with slug '{store_slug}' not found. Cannot add store preference.")
        return

    # Add the store to the user's preferences
    user.selected_stores.append(store_obj)
    logger.info(f"✅ Added '{store_slug}' to user '{username}' preferences.")


@db_query
def remove_user_store(username: str, store_slug: str, session) -> None:
    """
    Removes a store from the user's selected stores.

    Args:
        username (str): The username of the user.
        store_slug (str): The slug of the store to remove.
        session (Session): The database session (injected by the db_query decorator).

    Logs:
        Success or failure of the store removal operation.
    """
    user = session.query(User).options(joinedload(User.selected_stores)).filter(User.username == username).first()
    if not user:
        logger.warning(f"User '{username}' not found. Cannot remove store preference.")
        return

    # Find the specific store object in the user's collection to remove it
    store_to_remove = next((s for s in user.selected_stores if s.slug == store_slug), None)

    if store_to_remove:
        user.selected_stores.remove(store_to_remove)
        logger.info(f"✅ Removed '{store_slug}' from user '{username}' preferences.")
    else:
        logger.warning(f"User '{username}' does not have preference for store '{store_slug}'. Cannot remove.")



@db_query
def get_user_for_display(username: str, session) -> Optional[schema.UserPublicSchema]:
    """
    Retrieve a user by username from the database, excluding sensitive fields, and return as a UserPublicSchema instance.

    Args:
        username (str): The unique username of the user to fetch.
        session: The database session, injected by the db_query decorator.

    Returns:
        UserPublicSchema or None: The user data as a UserPublicSchema if found, otherwise None.

    Logs:
        Success or failure of the user retrieval operation.
    """
    user_orm = session.query(User).where(User.username == username).first()
    if user_orm:
        logger.info(f"✅ User '{username}' retrieved successfully.")
        return schema.UserPublicSchema.model_validate(user_orm)
    logger.warning(f"❌ User '{username}' not found.")
    return None


@db_query
def get_all_users(session) -> List[schema.UserPublicSchema]:
    """
    Retrieve all users from the database, excluding sensitive fields.

    Args:
        session: The database session, injected by the db_query decorator.

    Returns:
        List[UserPublicSchema]: A list of all users as UserPublicSchema instances.
    """
    users_orm = session.query(User).all()
    return [schema.UserPublicSchema.model_validate(user) for user in users_orm]


@db_query
def get_users_tracking_card(card_name: str, session) -> list[schema.UserPublicSchema]:
    """
    Finds all users who are tracking a specific card.
    
    Args:
        card_name (str): The name of the card to search for.
        session: The database session, injected by the db_query decorator.

    Returns:
        list[schema.UserPublicSchema]: A list of User objects who are tracking the specified card.
    """
    users_orm = session.query(User).join(User.cards).filter(UserTrackedCards.card_name == card_name).all()
    return [schema.UserPublicSchema.model_validate(user) for user in users_orm]


@db_query
def get_tracking_users_for_cards(card_names: list[str], session) -> dict[str, list[schema.UserPublicSchema]]:
    """
    Efficiently finds all users tracking any of the given card names.

    Args:
        card_names (list[str]): A list of card names to check.
        session: The database session, injected by the db_query decorator.

    Returns:
        dict[str, list[schema.UserPublicSchema]]: A dictionary mapping each card name to a list of User schemas.
    """
    if not card_names:
        return {}

    tracked_cards_with_users = (
        session.query(UserTrackedCards)
        .filter(UserTrackedCards.card_name.in_(card_names))
        .options(joinedload(UserTrackedCards.user))
        .all()
    )

    card_to_users_map = {name: [] for name in card_names}
    for tracked_card in tracked_cards_with_users:
        if tracked_card.user:
            user_schema = schema.UserPublicSchema.model_validate(tracked_card.user)
            card_to_users_map[tracked_card.card_name].append(user_schema)

    return card_to_users_map
