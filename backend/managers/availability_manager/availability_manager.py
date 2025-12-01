from typing import Dict

# Internal package imports
from . import availability_storage

# Manager package imports
from managers import user_manager
from managers import redis_manager

# Project package imports
from data import database
from schema import messaging
from utility import logger


def check_availability(username: str) -> Dict[str, str]:
    """Manually triggers an availability update for a user's card list."""
    logger.info(f"🔄 User {username} requested a manual availability refresh.")
    command = {
        "type": "queue_all_availability_checks",
        "payload": {"username": username},
    }
    redis_manager.publish_pubsub("scheduler-requests", command)
    logger.info(
        f"📢 Published 'queue_all_availability_checks' "
        f"command for user '{username}'."
    )
    return {
        "status": "requested",
        "message": "Availability update has been requested.",
    }


def trigger_availability_check_for_card(
    username: str, card_data: dict, on_complete_callback: callable = None
):
    """
    Forcefully triggers background availability checks for a single card
    against a user's preferred stores.
    This fulfills requirement [5.1.6] by always queueing a new check.
    """
    card_name = card_data.get("name")
    if not card_name:
        logger.error(
            "Cannot trigger availability check; "
            "card_data is missing 'name'."
        )
        return

    logger.info(
        f"Triggering availability check for '{card_name}' for '{username}'."
    )
    user_stores = database.get_user_stores(username)

    if not user_stores:
        logger.warning(
            f"User '{username}' has no preferred stores. "
            "Skipping automatic availability check."
        )
        return

    for store in user_stores:
        if not store or not store.slug:
            continue
        logger.debug(
            f"Publishing command to check '{card_name}' at '{store.slug}'."
        )
        payload = messaging.AvailabilityRequestPayload(
            username=username, store_slug=store.slug, card_data=card_data
        )
        command = messaging.SchedulerCommand(command="availability_request",
                                             payload=payload)
        redis_manager.publish_pubsub("scheduler-requests", command)

    # After queuing all tasks, call the callback if one was provided.
    # This is used to send the updated card list back to the user
    # at the right time.
    if on_complete_callback:
        on_complete_callback()


def get_cached_availability_or_trigger_check(username: str) -> Dict[str, dict]:
    """
    Orchestrates the availability check for all of a user's tracked cards.
    It returns any data found in the cache and queues background tasks for any
    non-cached items.
    """
    user_stores = database.get_user_stores(username)
    user_cards = user_manager.load_card_list(username)

    if not user_stores:
        logger.warning(
            f"User '{username}' has no stores configured."
            " Skipping availability check."
        )
        return {}

    cached_results = {}
    for card in user_cards:
        for store in user_stores:
            if not store or not store.slug or not card or not card.name:
                continue

            cached_data = availability_storage.get_cached_availability_data(
                store.slug, card.name
            )
            if cached_data is not None:
                logger.debug(
                    f"✅ Cache hit for {card.name} at {store.name}."
                )
                cached_results.setdefault(store.slug, {})[
                    card.name
                ] = cached_data
            else:
                logger.info(
                    f"⏳ Cache miss for {card.name} at {store.name}."
                    " Queueing check."
                )
                # Publish a command for the scheduler to queue the task.
                command = {
                    "type": "availability_request",
                    "payload": {
                        "username": username,
                        "store": store.slug,
                        "card_data": card.model_dump(),
                    },
                }
                redis_manager.publish_pubsub("scheduler-requests", command)

    return cached_results


def get_all_available_items_for_card(username: str, card_name: str) -> list:
    """
    Aggregates all available items for a single card from the cache across all
    of a user's preferred stores.
    This is used to populate the 'In Stock Details' modal on demand.
    """
    user_stores = database.get_user_stores(username)
    if not user_stores:
        logger.warning(
            f"User '{username}' has no stores configured."
            " Cannot get stock data."
        )
        return []

    all_available_items = []
    for store in user_stores:
        # Fetch from cache
        cached_data = availability_storage.get_cached_availability_data(
            store.slug, card_name
        )
        if cached_data:  # cached_data is a list of item dicts
            # Add the store name to each item before adding it to
            # the aggregated list.
            for item in cached_data:
                item_with_store = item.copy()
                item_with_store["store_name"] = store.name
                all_available_items.append(item_with_store)

    logger.info(
        f"Aggregated {len(all_available_items)} available items for"
        f" '{card_name}' for user '{username}'."
    )
    return all_available_items
