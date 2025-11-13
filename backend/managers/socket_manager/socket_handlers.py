from flask_login import current_user
from pydantic import ValidationError

from data import database
from data.database import exceptions
from managers import user_manager
from managers import availability_manager

from .socket_manager import socketio
from .socket_schemas import (
    AddCardSchema,
    UpdateCardSchema,
    DeleteCardSchema,
    GetPrintingsSchema,
    UpdateStoreSchema,
)
from utility import logger


def get_username():
    """Helper function to get the username from the current_user proxy."""
    if current_user.is_authenticated:
        return current_user.username
    return None


@socketio.on("get_card_printings")
def handle_get_card_printings(data: dict):
    """
    Handles a client's request for all valid printings of a specific card.
    Implements requirement [4.3.5].
    """
    validated_data = GetPrintingsSchema.model_validate(data)
    card_name = validated_data.card_name
    if not database.is_card_in_catalog(card_name):
        logger.info(f"{card_name} not in catalog")
        return

    printings = database.get_printings_for_card(card_name)
    payload = {"card_name": card_name, "printings": printings}
    socketio.emit("card_printings_data", payload)
    logger.info(f"📡 Sent {len(printings)} printings for '{card_name}'.")


def _send_user_cards(username: str):
    """Fetches a user's card list, formats it, and emits it over Socket.IO."""
    if not username:
        logger.error("❌ Attempted to send card list for an empty username.")
        return

    logger.info(f"📜 Fetching and sending tracked cards for user: {username}")
    cards = user_manager.load_card_list(username)

    # Build a complete list of all cards for the user.
    # user_manager.load_card_list returns an empty list if no cards are found.
    # The list comprehension will correctly handle an empty list.
    card_list = [
        {
            "card_name": card.card_name,
            "amount": card.amount,
            "specifications": (
                [
                    {
                        "set_code": spec.set_code,
                        "collector_number": spec.collector_number,
                        "finish": spec.finish,
                    }
                    for spec in card.specifications
                ]
                if card.specifications
                else []
            ),
        }
        for card in cards
        if card and card.card_name
    ]

    # Emit a single event with the entire list to the user's room.
    socketio.emit(
        "cards_data",
        {"username": username, "tracked_cards": card_list},
        room=username,
    )
    logger.info(
        f"📡 Sent card list to room '{username}' with {len(card_list)} items."
    )


def _send_user_stores(username: str):
    """Fetches a user's store list and emits it over Socket.IO."""
    if not username:
        logger.error("❌ Attempted to send store list for an empty username.")
        return

    logger.info(f"🏬 Fetching and sending tracked stores for user: {username}")
    stores = database.get_user_stores(username)
    # The stores from the DB are Pydantic models, so we can dump them to dicts.
    store_list = [store.model_dump() for store in stores]

    socketio.emit("user_stores_data", {"stores": store_list}, room=username)
    logger.info(
        f"📡 Sent store list to room '{username}' with {len(store_list)} items."
    )


@socketio.on("get_card_availability")
def handle_get_card_availability(data: dict = None):
    """
    Handles a front-end request for updated card availability data.
    If `data` is provided, it can be used to check a specific card.
    If `data` is None, it checks all tracked cards for the user.
    """
    logger.info(f"📩 Received 'get_card_availability' request. Data: {data}")
    username = get_username()
    if username:
        logger.info(f"🔍 Fetching card availability for user: {username}")
        # TODO: In the future, use the `data` payload to check a specific card.
        # For now, this function triggers a check for all cards.
        #    items and returns any data that was already in the cache.
        cached_data = (
            availability_manager.get_cached_availability_or_trigger_check(
                username
            )
        )

        # 2. Immediately send any cached data back to the client.
        if cached_data:
            logger.info(
                f"📡 Sending "
                f"{sum(len(cards) for cards in cached_data.values())} "
                f"cached availability items to user '{username}'."
            )
            # The data is structured as {store_slug: {card_name: items}}.
            # We need to emit it in the format the frontend expects:
            # one event per item.
            for store_slug, cards in cached_data.items():
                for card_name, items in cards.items():
                    event_data = {
                        "username": username,
                        "store": store_slug,
                        "card": card_name,
                        "items": items,
                    }
                    socketio.emit(
                        "card_availability_data", event_data, room=username
                    )
        else:
            logger.info(
                f"No cached availability data found for user '{username}'."
            )

        logger.info(
            "✅ Card availability check process initiated for user "
            f"'{username}'."
        )
    else:
        logger.warning(
            "🚨 No username found for 'get_card_availability' request."
        )


@socketio.on("get_cards")
def handle_get_cards():
    """Handles a request to retrieve the user's tracked cards."""
    logger.info("📩 Received 'get_cards' request from front end.")
    username = get_username()
    if username:
        _send_user_cards(username)
    else:
        logger.warning("🚨 No username found for 'get_cards' request.")


@socketio.on("search_card_names")
def handle_search_card_names(data: dict):
    """Handles a request to search for card names based on a query string."""
    logger.info("📩 Received 'search_card_names' request from front end.")
    query = data.get("query", "").strip()
    if not query or len(query) < 3:
        socketio.emit(
            "card_name_search_results", {"query": query, "card_names": []}
        )
        return

    logger.info(f"🗂️ Searching for card names matching '{query}'...")
    try:
        card_names = database.search_card_names(query, limit=10)
        socketio.emit(
            "card_name_search_results",
            {"query": query, "card_names": card_names},
        )
        logger.info(f"📡 Sent {len(card_names)} search results for '{query}'.")
    except Exception as e:
        logger.error(f"❌ Failed to search for card names: {e}")
        socketio.emit(
            "card_name_search_results", {"query": query, "card_names": []}
        )


@socketio.on("add_card")
def handle_add_user_tracked_card(data: dict):
    logger.info("📩 Received 'add_card' request from front end.")
    """Add tracked card to the database and send an updated card list."""
    try:
        validated_data = AddCardSchema.model_validate(data)
        username = get_username()
        if not username:
            logger.warning("🚨 Unauthenticated user tried to add a card.")
            socketio.emit(
                "error", {"message": "Authentication required to add cards."}
            )
            return

        user_manager.add_user_card(
            username,
            validated_data.card,
            validated_data.amount,
            validated_data.card_specs,
        )

        # Delegate to the availability manager to trigger the check
        # adhering to data flow rules.
        card_data_for_task = {
            "card_name": validated_data.card,
            "specifications": validated_data.card_specs,
        }
        # Pass _send_user_cards as a callback to be executed *after*
        # the availability checks have been queued. This ensures the
        # frontend receives events in the correct order.
        availability_manager.trigger_availability_check_for_card(
            username,
            card_data_for_task,
            on_complete_callback=lambda: _send_user_cards(username),
        )
    except ValidationError as e:
        logger.error(f"❌ Invalid 'add_card' data received: {e}")
        socketio.emit("error", {"message": f"Invalid data for add_card: {e}"})
    except exceptions.InvalidSpecificationError as e:
        logger.warning(
            f"⚠️ User '{username}' submitted an invalid card specification: "
            f"{e}"
        )
        # Send a specific, user-friendly error message to the client.
        socketio.emit("error", {"message": str(e)})


@socketio.on("delete_card")
def handle_delete_user_tracked_card(data: dict):
    logger.info("📩 Received 'delete_card' request from front end.")
    try:
        validated_data = DeleteCardSchema.model_validate(data)
        username = get_username()
        if not username:
            logger.warning("🚨 Unauthenticated user tried to delete a card.")
            socketio.emit(
                "error", {"message":
                          "Authentication required to delete cards."}
            )
            return

        database.delete_user_card(username, validated_data.card)
        _send_user_cards(username)
    except ValidationError as e:
        logger.error(f"❌ Invalid 'delete_card' data received: {e}")
        socketio.emit(
            "error", {"message": f"Invalid data for delete_card: {e}"}
        )


@socketio.on("update_card")
def handle_update_user_tracked_cards(data: dict):
    logger.info("📩 Received 'update_card' request from front end.")
    try:
        validated_data = UpdateCardSchema.model_validate(data)
        username = get_username()
        if not username:
            logger.warning("🚨 Unauthenticated user tried to update a card.")
            socketio.emit(
                "error", {"message":
                          "Authentication required to update cards."}
            )
            return

        database.update_user_tracked_card_preferences(
            username, validated_data.card, validated_data.update_data
        )
        _send_user_cards(username)
    except ValidationError as e:
        logger.error(f"❌ Invalid 'update_card' data received: {e}")
        socketio.emit(
            "error", {"message": f"Invalid data for update_card: {e}"}
        )


@socketio.on("update_stores")
def handle_update_user_stores(data: dict):
    """
    Handles a request to update the user's entire list of preferred stores.
     Implements requirement [4.3.6]."""
    logger.info(
        f"📩 Received 'update_stores' request from front end. Data: {data}"
    )
    username = get_username()
    if not username:
        logger.warning("🚨 No username found for 'update_stores' request.")
        return

    try:
        validated_data = UpdateStoreSchema.model_validate(data)
        database.set_user_stores(username, validated_data.stores)
        _send_user_stores(username)
        logger.info(f"✅ Updated preferred stores for user '{username}'.")
    except ValidationError as e:
        logger.error(f"❌ Invalid 'update_stores' data received: {e}")
        socketio.emit(
            "error", {"message": f"Invalid data for update_stores: {e}"}
        )


@socketio.on("stock_data_request")
def handle_stock_data_request(data: dict):
    """ """
    logger.info(
        f"📩 Received 'stock_data_request' request from front end. Data: {data}"
    )
    username = get_username()
    if not username:
        logger.warning("🚨 No username found for 'stock_data_request' request.")
        return

    card_name = data.get("card_name")
    if not card_name:
        logger.error("❌ 'stock_data_request' received without 'card_name'.")
        socketio.emit(
            "error", {"message": "Card name is required to get stock data."}
        )
        return

    logger.info(
        f"🔍 Aggregating all available items for '{card_name}' for user "
        f"'{username}'."
    )
    all_available_items = \
        availability_manager.get_all_available_items_for_card(
            username, card_name
        )
    # Emit the aggregated data back to the client.
    socketio.emit(
        "stock_data",
        {"card_name": card_name, "items": all_available_items},
        room=username,
    )
    logger.info(
        f"📡 Sent {len(all_available_items)} aggregated stock items for "
        f"'{card_name}' to user '{username}'."
    )
