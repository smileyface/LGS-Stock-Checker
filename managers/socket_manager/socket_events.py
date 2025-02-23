from flask_socketio import emit

from managers.store_manager import get_cached_availability
from managers.user_manager import get_selected_stores
from managers.user_manager.user_manager import load_card_list
from utility.logger import logger
from worker.tasks import update_availability


def send_card_availability_update(username):
    """
    Fetch the latest cached card availability and send it to the client.
    If data is stale or missing, Redis tasks are already queued to refresh it.
    """
    logger.info(f"📩 Received request for card availability update from {username}")

    # Retrieve cached data first
    user_cards = load_card_list(username)
    selected_stores = get_selected_stores(username)

    if not user_cards:
        logger.warning(f"🚨 No tracked cards found for {username}. Skipping availability update.")
        return

    if not selected_stores:
        logger.warning(f"🚨 No selected stores for {username}. Skipping availability update.")
        return

    # Aggregate cached availability
    availability_data = []
    for card in user_cards:
        cached_availability = get_cached_availability(card["card_name"])  # Fetch from cache
        filtered_availability = {
            store: details for store, details in cached_availability.items() if store in selected_stores
        }

        if filtered_availability:
            availability_data.append({
                "card_name": card["card_name"],
                "stores": filtered_availability
            })

    # Send cached availability data immediately
    emit("card_availability_data", availability_data, broadcast=True)
    logger.info(f"📡 Sent cached availability update for {username} with {len(availability_data)} available cards")


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
