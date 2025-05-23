from flask_socketio import emit

from externals import fetch_scryfall_card_names
from managers.availability_manager import get_card_availability
from managers.user_manager import load_card_list
from utility.logger import logger


def send_full_card_list():
    """Send cached card names to the frontend via WebSocket."""
    logger.info("📩 Fetching full cached card list from Redis...")

    try:
        card_names = fetch_scryfall_card_names()

        if not card_names:
            logger.warning("⚠️ Cached card list is empty or unavailable.")
            card_names = []  # Ensure frontend gets an empty list instead of None

        emit("card_names_response", {"card_names": card_names})
        logger.info(f"📡 Sent {len(card_names)} card names to frontend.")

    except Exception as e:
        logger.error(f"❌ Failed to retrieve card names from Redis: {e}")
        emit("card_names_response", {"card_names": []})  # Send empty list on failure


def send_card_availability_update(username):
    """
    Fetch the latest card availability state and send it to the client.
    """
    logger.info(f"📩 Received request for card availability update from {username}")

    availability = get_card_availability(username)
    if availability is []:
        logger.info(f"🚨 No availability data found for {username}.")
        emit("no_availability", None, broadcast=True)
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

    card_list = [
        {
            "card_name": card.card_name,
            "amount": card.amount,
            "specifications": [
                {"set_code": spec.set_code, "collector_number": spec.collector_number, "finish": spec.finish}
                for spec in card.specifications
            ] if card.specifications else [],
        }
        for card in cards
    ]

    emit("cards_data", {"username": username, "tracked_cards": card_list})
    logger.info(f"📡 Sent card list for {username} with {len(card_list)} items")
