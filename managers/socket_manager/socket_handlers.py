from flask import session

from managers.card_manager import parse_card_list
from managers.socket_manager.socket_events import send_card_availability_update, send_card_list, send_full_card_list
from managers.socket_manager.socket_manager import socketio
import data.database as db
from utility.logger import logger


def get_username():
    """Helper function to get the username from the session."""
    return session.get("username")


@socketio.on("get_card_availability")
def handle_get_card_availability():
    """Handles a front-end request for updated card availability data."""
    logger.info("📩 Received 'get_card_availability' request from front end.")
    username = get_username()
    if username:
        logger.info(f"🔍 Fetching card availability for user: {username}")
        send_card_availability_update(username)
    else:
        logger.warning("🚨 No username found for 'get_card_availability' request.")


@socketio.on("get_cards")
def handle_get_cards():
    """Handles a request to retrieve the user's tracked cards."""
    logger.info("📩 Received 'get_cards' request from front end.")
    username = get_username()
    if username:
        logger.info(f"📜 Sending tracked cards list for user: {username}")
        send_card_list(username)
    else:
        logger.warning("🚨 No username found for 'get_cards' request.")


@socketio.on("parse_card_list")
def handle_parse_card_list(data):
    """Handles a request to parse a raw card list input."""
    logger.info("📩 Received 'parse_card_list' request from front end.")
    if "raw_list" in data:
        logger.info("📝 Parsing raw card list from user input.")
        parsed_cards = parse_card_list(data["raw_list"])
        socketio.emit("parsed_cards", {"cards": parsed_cards})
        logger.info("✅ Parsed card list sent to front end.")
    else:
        logger.warning("🚨 'parse_card_list' request missing 'raw_list' field.")


@socketio.on("request_card_names")
def handle_request_card_names():
    logger.info("📩 Received 'request_card_names' request from front end.")
    """Send cached card names to the frontend via WebSocket."""
    send_full_card_list()


@socketio.on("add_card")
def handle_add_user_tracked_card(data):
    logger.info("📩 Received 'add_card' request from front end.")
    """Add tracked card to the database and send an updated card list."""
    db.add_user_card(get_username(), data["card"], data["amount"], data["card_specs"])
    handle_get_cards()


@socketio.on("delete_card")
def handle_delete_user_tracked_card(data):
    logger.info("📩 Received 'delete_card' request from front end.")
    db.delete_user_card(get_username(), data["card"])
    handle_get_cards()


@socketio.on("update_card")
def handle_update_user_tracked_cards(data):
    logger.info("📩 Received 'update_card' request from front end.")
    db.update_user_tracked_card_preferences(get_username(), data["card"], data["update_data"])
    handle_get_cards()
