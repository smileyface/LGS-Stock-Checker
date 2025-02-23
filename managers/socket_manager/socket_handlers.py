from managers.card_manager import parse_card_list
from managers.socket_manager.socket_manager import socketio
from flask import session
from managers.redis_manager import redis_manager
from managers.socket_manager.socket_events import send_card_availability_update, send_card_list
from utility.logger import logger
from worker.tasks import update_availability


def get_username():
    """Helper function to get the username from the session."""
    return session.get("username")


@socketio.on("get_card_availability")
def handle_get_card_availability():
    """Handles a front-end request for updated card availability data."""
    logger.info("📩 Received 'get_card_availability' request from front end.")

    username = get_username()
    if not username:
        logger.warning("🚨 No username found for 'get_card_availability' request.")
        return

    logger.info(f"🔍 Fetching card availability for user: {username}")

    # Send cached availability first
    send_card_availability_update(username)

    # Queue async updates for stale/missing data
    update_availability(username)  # 🔄 Ensure fresh data is retrieved

    logger.info(f"📌 Queued async availability check for {username}")


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



def handle_save_cards():
    return None