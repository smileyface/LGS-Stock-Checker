"""
Manages a user's tracked card list, including adding, updating, deleting,
and sending updates back to the client.
"""
from data import database
from utility import logger
from managers.socket_manager import socketio


def _send_updated_card_list(username: str):
    """
    Fetches the user's full card list and emits it to the client.
    This is the single source of truth for updating the frontend table.
    """
    logger.info(f"📜 Fetching and sending updated tracked cards for user: {username}")
    cards = database.get_users_cards(username)

    # Serialize the list of Pydantic objects into a JSON-serializable format.
    # This is crucial for the data to be correctly interpreted by the frontend.
    card_list = [
        {
            "card_name": card.card_name,
            "amount": card.amount,
            "specifications": [
                {
                    "set_code": spec.set_code,
                    "collector_number": spec.collector_number,
                    "finish": spec.finish,
                } for spec in card.specifications
            ] if card.specifications else [],
        } for card in cards
    ]

    socketio.emit("cards_data", {"tracked_cards": card_list}, room=username)
    logger.info(f"📡 Sent updated card list to room '{username}' with {len(card_list)} items.")


def add_user_card(username: str, card_name: str, amount: int, card_specs: dict):
    """Adds a card to a user's list and sends an update."""
    logger.info(f"Adding card '{card_name}' for user '{username}'.")
    # Pass the arguments individually to the data layer function.
    database.add_user_card(username, card_name, amount, card_specs)
    _send_updated_card_list(username)


def update_user_card(username: str, card_name: str, update_data: dict):
    """Updates a card in a user's list and sends an update."""
    logger.info(f"Updating card '{card_name}' for user '{username}'.")
    database.update_user_tracked_card_preferences(username, card_name, update_data)
    _send_updated_card_list(username)


def delete_user_card(username: str, card_name: str):
    """Deletes a card from a user's list and sends an update."""
    logger.info(f"Deleting card '{card_name}' for user '{username}'.")
    database.delete_user_card(username, card_name)
    _send_updated_card_list(username)


def load_card_list(username: str):
    """Loads a user's card list from the database without sending an update."""
    logger.info(f"📖 Loading card list for user: '{username}'")
    if not database.get_user_by_username(username):
        logger.warning(f"User '{username}' not found when trying to load card list.")
        return []
    
    cards = database.get_users_cards(username)
    logger.info(f"✅ Loaded {len(cards)} cards for user: '{username}'")
    return cards
