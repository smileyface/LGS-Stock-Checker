from flask_socketio import emit

from managers.availability_manager.availability_manager import check_availability
from managers.user_manager.user_manager import load_card_list
from utility.logger import logger


def send_card_availability_update(username):
    """
    Fetch the latest card availability state and send it to the client.
    """
    logger.info(f"📩 Received request for card availability update from {username}")

    availability = check_availability(username)
    if availability is None:
        logger.warning(f"🚨 No availability data found for {username}")
        return

    emit("card_availability_data", availability, broadcast=True)
    logger.info(f"📡 Sent card availability update for {username} with {len(availability)} available")


def send_card_list(username):
    """
    Fetches the user's tracked cards from the correct manager and sends them.
    """
    logger.info(f"📩 Received request for tracked card list from {username}")

    if not username:
        emit("error", {"message": "Username is required"}, namespace="/")
        logger.error("❌ Error: Username is missing in get_cards request")
        return

    cards = load_card_list(username)
    if cards is None:
        logger.warning(f"🚨 No tracked cards found for {username}")
        return

    emit("cards_data", {"username": username, "tracked_cards": cards})
    logger.info(f"📡 Sent card list for {username} with {len(cards)} items")
