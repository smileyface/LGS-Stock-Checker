"""
Module: backend.tasks.card_availability_tasks

High-level overview
-------------------
Background task definitions used to orchestrate availability checks for trading
cards across user-tracked card lists and configured stores. Tasks interact with
the database, user and store managers, a Redis pub/sub channel for
inter-process coordination, and a socket emitter to notify clients in real
time.

Key responsibilities
- Aggregate wanted cards across users.
- Fan-out availability check requests for all users or a single user.
- Execute a worker task to fetch availability for a single card/store pair,
    publish results for backend consumption, and emit live updates to clients.

Important side-effects
- Publishes commands and results to Redis topics (e.g. "scheduler-requests",
    "worker-results") to coordinate work between scheduler, workers,
    and the main application.
- Emits socket events (via socket_emit.emit_from_worker) to notify clients
    about the start and results of availability checks.
- Reads user, card, and store configuration from persistent managers and the
    database; relies on store implementations to perform remote availability
    lookups.

This module fulfills requirements [5.1.7] and related functionality.
    """

from data import database
from managers import store_manager, user_manager, task_manager, redis_manager
from managers.socket_manager import socket_emit
from schema import messaging
from utility import logger


def get_wanted_cards(users: list):
    """Aggregates all cards that users have in their wanted lists."""
    logger.info(
        f"📌 Starting wanted cards aggregation for {len(users)} user(s)..."
    )

    wanted_cards = set()

    for user in users:
        username = user.username
        if not username:
            continue
        logger.debug(f"📖 Loading card list for user '{username}'")

        user_cards = user_manager.load_card_list(username)

        for card in user_cards:
            card_name = card.card_name
            if not card_name:
                logger.warning(
                    f"❌ Card '{card_name}' in user '{username}' has a "
                    f"null card name. Skipping."
                )
                continue
            wanted_cards.add(card_name)
            logger.debug(f"➕ Added '{card_name}' to wanted cards set.")

    logger.info(
        f"✅ Aggregation complete. Total unique wanted cards: "
        f"{len(wanted_cards)}"
    )
    return list(wanted_cards)


@task_manager.task()
def update_all_tracked_cards_availability():
    """
    System-wide task to re-check availability for all tracked cards for
    all users. This acts as a fan-out task, enqueuing specific checks for each
    user/card/store combo.
    This fulfills requirement [5.1.7].
    """
    logger.info(
        "🚀 Starting system-wide availability check for all tracked cards."
    )
    try:
        all_users = database.get_all_users()
        if not all_users:
            logger.info(
                "No users found. Skipping system-wide availability check."
            )
            return

        for user in all_users:
            logger.debug(
                f"Queueing availability checks for user: {user.username}"
            )
            # This re-uses the existing on-demand logic for a specific user.
            update_availability_for_user(user.username)

    except Exception as e:
        logger.error(
            f"❌ An error occurred during system-wide availability check: {e}",
            exc_info=True,
        )


@task_manager.task(
    task_manager.task_definitions.UPDATE_WANTED_CARDS_AVAILABILITY
)
def update_availability_for_user(username: str):
    """
    Checks availability for all tracked cards for a *specific user*
    against their preferred stores. This is triggered on-demand
    (e.g., after login).
    """
    logger.info(f"🔄 Starting availability check for user: {username}")
    user_cards = user_manager.load_card_list(username)
    user_stores = database.get_user_stores(username)

    if not user_cards or not user_stores:
        logger.warning(
            f"User '{username}' has no cards or stores to check. Skipping."
        )
        return False

    for card in user_cards:
        for store in user_stores:
            command = {
                "type": "availability_request",
                "payload": {
                    "username": username,
                    "store": store.slug,
                    "card_data": card.model_dump(),
                },
            }
            redis_manager.publish_pubsub("scheduler-requests", command)
            logger.debug(
                f"📢 Published 'availability_request' command for"
                f" '{card.card_name}' at '{store.slug}'."
            )


@task_manager.task(
    task_manager.task_definitions.UPDATE_AVAILABILITY_SINGLE_CARD
)
def update_availability_single_card(username: str,
                                    store_name: str,
                                    card: dict) -> bool:
    """
    Background task to update the availability for a single card at a store.
    """
    if not store_name:
        logger.warning(f"🚨 Invalid store name: {store_name}. Task aborted.")
        return False
    card_name = card.get("name")
    if not card_name:
        logger.error(
            f"❌ Task received card data without a 'card_name'. "
            f"Aborting. Data: {card}"
        )
        return False
    # --- Emit start event to client ---
    socket_emit.emit_from_worker(
        "availability_check_started",
        {"store": store_name, "card": card_name},
        room=username,
    )

    logger.info(
        f"📌 Task started: Updating availability for {card_name} "
        f"at {store_name} (User: {username})"
    )

    # Ensure store_name is in the correct format
    store = store_manager.get_store(store_name)
    if not store:
        logger.warning(
            f"🚨 Store '{store_name}' is not configured or missing "
            f"from STORE_REGISTRY. Task aborted."
        )
        return False

    logger.info(f"🔍 Checking availability for {card_name} at {store_name}")

    # Fetch availability using the specific store's implementation
    card_specs = card.get("card_specs")
    available_items = store.fetch_card_availability(card_name, card_specs)

    if available_items:
        logger.info(
            f"✅ Found {len(available_items)} listings for {card_name} "
            f"at {store_name}. Caching and emitting."
        )
    else:
        logger.info(
            f"ℹ️ No available listings found for {card_name} "
            f"at {store_name}. Caching empty result."
        )

    redis_manager.publish_pubsub(
        messaging.generator.GenerateAvailabilityResult(
            card={"card": {
                "name": card_name,
                "card_specs": card_specs or []
            }
            },
            store={
                "slug": store_name},
            items=available_items
        )
    )

    # --- Emit results to the client ---
    # The worker still emits directly to the client for real-time UI updates.
    event_data = {
        "username": username,
        "store": store_name,
        "card": card_name,
        "items": available_items or [],
    }
    socket_emit.emit_from_worker(
        "card_availability_data", event_data, room=username
    )
    return True


@task_manager.task(
    task_manager.task_definitions.AVAILABILITY_TASK_ID
)
def queue_all_availability_checks():
    tracked_cards = database.get_all_tracked_cards()
    if not tracked_cards:
        logger.info("No cards tracked")
        return

    all_users = database.get_all_users()
    if not all_users:
        logger.info("No users found")
        return

    for card in tracked_cards:
        username = database.get_user_orm_by_id(card.user_id).username
        if not username:
            logger.warning("username does not exist")

        card_data = {
            "card_name": card.card_name,
            "amount": card.amount,
            # Hardcoded for now. Will be updated when specifications are more
            #  implemented
            "specifications": None
        }
        store_name = card.store.slug

        redis_manager.publish_pubsub(
            messaging.GenerateAvailabilityRequestCommand(
                username,
                store_name,
                card_data
            )
        )
