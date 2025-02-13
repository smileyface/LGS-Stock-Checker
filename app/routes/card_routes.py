from flask_socketio import SocketIO, emit
from flask import session, request, Blueprint
from managers.card_manager.card_manager import parse_card_list, load_card_list, save_card_list

socketio = SocketIO()
card_bp = Blueprint("card_bp", __name__)
@socketio.on('get_cards')
def handle_get_cards():
    username = session.get('username')
    if username:
        card_list = load_card_list(username)
        emit('cards_data', {'cards': card_list})
    else:
        emit('cards_data', {'error': 'User not logged in'})

@socketio.on('save_cards')
def handle_save_cards(data):
    username = session.get('username')
    if username:
        save_card_list(username, data.get('cards', []))
        emit('cards_saved', {'message': 'Card list updated successfully'})
    else:
        emit('cards_saved', {'error': 'User not logged in'})

@socketio.on('parse_card_list')
def handle_parse_card_list(data):
    parsed_cards = parse_card_list(data.get('raw_list', ''))
    emit('parsed_cards', {'cards': parsed_cards})
