from flask_socketio import emit
from flask import request

# Store active WebSocket connections
connected_clients = set()


def handle_connect():
    """Handle new WebSocket connections."""
    print(f"🟢 Client connected: {request.sid}")
    connected_clients.add(request.sid)


def handle_disconnect():
    """Handle WebSocket disconnections."""
    print(f"🔴 Client disconnected: {request.sid}")
    connected_clients.discard(request.sid)
