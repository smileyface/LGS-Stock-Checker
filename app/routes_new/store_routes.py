from flask_socketio import SocketIO, emit
from flask import session, request, Blueprint, render_template
from core.store_manager import STORE_REGISTRY
from managers.user_manager.user_manager import get_user, update_selected_stores

socketio = SocketIO()


store_bp = Blueprint("store_bp", __name__)

@store_bp.route("/stores")
def stores():
    return render_template("stores.html")

@socketio.on('get_stores')
def handle_get_stores():
    username = session.get('username')
    if username:
        user = get_user(username)
        all_stores = list(STORE_REGISTRY.keys())
        emit('stores_data', {'all_stores': all_stores, 'selected_stores': user.get('selected_stores', [])})
    else:
        emit('stores_data', {'error': 'User not logged in'})

@socketio.on('update_stores')
def handle_update_stores(data):
    username = session.get('username')
    if username:
        selected_stores = data.get('stores', [])
        update_selected_stores(username, selected_stores)
        emit('stores_updated', {'message': 'Stores updated successfully'})
    else:
        emit('stores_updated', {'error': 'User not logged in'})
