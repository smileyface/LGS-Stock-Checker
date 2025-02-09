from .socket_connections import handle_connect, handle_disconnect
from .socket_events import send_inventory_update
from flask_socketio import SocketIO
from managers.redis_manager.redis_manager import REDIS_URL

# Initialize Flask-SocketIO
socketio = SocketIO(
    message_queue=REDIS_URL,
    cors_allowed_origins="*",
    async_mode="eventlet"
)

__all__ = ["socketio", "handle_connect", "handle_disconnect", "send_inventory_update"]