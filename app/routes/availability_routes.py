from flask_socketio import SocketIO, emit
from flask import session, Blueprint
from worker.tasks import update_availability, update_availability_single_card

socketio = SocketIO()

availability_bp = Blueprint("availability_bp", __name__)

@socketio.on('connect')
def handle_connect():
    print(f'User connected: {session.get("username", "Guest")}')

@socketio.on('update_availability')
def handle_update_availability():
    update_availability()
    emit('availability_updated', {'message': 'Availability data refreshed'}, broadcast=True)

@socketio.on('update_card_availability')
def handle_update_card_availability(card_id):
    update_availability_single_card(card_id)
    emit('card_availability_updated', {'card_id': card_id}, broadcast=True)
