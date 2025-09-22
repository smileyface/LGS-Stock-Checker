from pydantic import BaseModel, ValidationError
from typing import List
from flask_login import current_user

# internal package imports
from .socket_manager import socketio
from .socket_schemas import (
    AddCardSchema,
    DeleteCardSchema,
    ParseCardListSchema,
    UpdateCardSchema,
    UpdateStoresSchema,
)

# manager package imports
import managers.card_manager as card_manager
import managers.user_manager as user_manager
import managers.availability_manager as availability_manager

# project package imports
from externals import fetch_scryfall_card_names
from data import database
from utility import logger


def get_username():
    """Helper function to get the username from the current_user proxy."""
    if current_user.is_authenticated:
        return current_user.username
    return None


def _send_user_cards(username: str):
    """Fetches a user's card list, formats it, and emits it over Socket.IO."""
    if not username:
        logger.error("❌ Attempted to send card list for an empty username.")
        return

    logger.info(f"📜 Fetching and sending tracked cards for user: {username}")
    cards = user_manager.load_card_list(username)

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
    ]

    # Emit to the user's room to update all of their connected clients.
    socketio.emit(
        "cards_data", {"username": username, "tracked_cards": card_list}, room=username
    )
    logger.info(f"📡 Sent card list to room '{username}' with {len(card_list)} items.")


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
    logger.info(f"📡 Sent store list to room '{username}' with {len(store_list)} items.")


@socketio.on("get_card_availability")
def handle_get_card_availability():
    """Handles a front-end request for updated card availability data."""
    logger.info("📩 Received 'get_card_availability' request from front end.")
    username = get_username()
    if username:
        logger.info(f"🔍 Fetching card availability for user: {username}")
        # This function queues background tasks to check for availability.
        # It returns a status message that we can forward to the client.
        result = availability_manager.get_card_availability(username)
        socketio.emit("availability_check_status", result, room=username)
        logger.info(
            f"✅ Card availability check initiated for user {username}. Status: {result.get('message')}"
        )
    else:
        logger.warning("🚨 No username found for 'get_card_availability' request.")


@socketio.on("get_cards")
def handle_get_cards():
    """Handles a request to retrieve the user's tracked cards."""
    logger.info("📩 Received 'get_cards' request from front end.")
    username = get_username()
    if username:
        _send_user_cards(username)
    else:
        logger.warning("🚨 No username found for 'get_cards' request.")


@socketio.on("parse_card_list")
def handle_parse_card_list(data: dict):
    """Handles a request to parse a raw card list input."""
    logger.info("📩 Received 'parse_card_list' request from front end.")
    try:
        validated_data = ParseCardListSchema.model_validate(data)
        logger.info("📝 Parsing raw card list from user input.")
        parsed_cards = card_manager.parse_card_list(validated_data.raw_list)
        socketio.emit("parsed_cards", {"cards": parsed_cards})
        logger.info("✅ Parsed card list sent to front end.")
    except ValidationError as e:
        logger.error(f"❌ Invalid 'parse_card_list' data received: {e}")
        socketio.emit("error", {"message": f"Invalid request: {e}"})


@socketio.on("request_card_names")
def handle_request_card_names():
    logger.info("📩 Received 'request_card_names' request from front end.")
    # Send cached card names to the frontend via WebSocket.
    logger.info("🗂️ Fetching full cached card list from Redis...")

    try:
        card_names = fetch_scryfall_card_names()

        if not card_names:
            logger.warning("⚠️ Cached card list is empty or unavailable.")
            card_names = []  # Ensure frontend gets an empty list instead of None

        socketio.emit("card_names_response", {"card_names": card_names})
        logger.info(f"📡 Sent {len(card_names)} card names to frontend.")

    except Exception as e:
        logger.error(f"❌ Failed to retrieve card names from Redis: {e}")
        socketio.emit(
            "card_names_response", {"card_names": []}
        )  # Send empty list on failure


@socketio.on("add_card")
def handle_add_user_tracked_card(data: dict):
    logger.info("📩 Received 'add_card' request from front end.")
    """Add tracked card to the database and send an updated card list."""
    try:
        validated_data = AddCardSchema.model_validate(data)
        username = get_username()
        user_manager.add_user_card(
            username,
            validated_data.card,
            validated_data.amount,
            validated_data.card_specs,
        )
        _send_user_cards(username)
    except ValidationError as e:
        logger.error(f"❌ Invalid 'add_card' data received: {e}")
        socketio.emit("error", {"message": f"Invalid data for add_card: {e}"})


@socketio.on("delete_card")
def handle_delete_user_tracked_card(data: dict):
    logger.info("📩 Received 'delete_card' request from front end.")
    try:
        validated_data = DeleteCardSchema.model_validate(data)
        username = get_username()
        database.delete_user_card(username, validated_data.card)
        _send_user_cards(username)
    except ValidationError as e:
        logger.error(f"❌ Invalid 'delete_card' data received: {e}")
        socketio.emit("error", {"message": f"Invalid data for delete_card: {e}"})


@socketio.on("update_card")
def handle_update_user_tracked_cards(data: dict):
    logger.info("📩 Received 'update_card' request from front end.")
    try:
        validated_data = UpdateCardSchema.model_validate(data)
        username = get_username()
        database.update_user_tracked_card_preferences(
            username, validated_data.card, validated_data.update_data
        )
        _send_user_cards(username)
    except ValidationError as e:
        logger.error(f"❌ Invalid 'update_card' data received: {e}")
        socketio.emit("error", {"message": f"Invalid data for update_card: {e}"})


@socketio.on("update_stores")
def handle_update_user_stores(data: dict):
    """Handles a request to update the user's entire list of preferred stores."""
    logger.info(f"📩 Received 'update_stores' request from front end. Data: {data}")
    username = get_username()
    if not username:
        logger.warning("🚨 No username found for 'update_stores' request.")
        return

    try:
        validated_data = UpdateStoresSchema.model_validate(data)
        database.set_user_stores(username, validated_data.stores)
        _send_user_stores(username)
        logger.info(f"✅ Updated preferred stores for user '{username}'.")
    except ValidationError as e:
        logger.error(f"❌ Invalid 'update_stores' data received: {e}")
        socketio.emit("error", {"message": f"Invalid data for update_stores: {e}"})
