import json
from unittest.mock import call, ANY

# The main socketio instance from the application
from managers.socket_manager import socketio


def test_anonymous_websocket_connection_lifecycle(app, client, mocker):
    """
    GIVEN a new, unauthenticated client
    WHEN the client establishes a WebSocket connection
    THEN the server should log an anonymous connection and keep it open
    AND WHEN the client disconnects
    THEN the server should log the disconnection.
    """
    # Arrange: Spy on the logger within the socket_connections module
    mock_logger = mocker.patch(
        "managers.socket_manager.socket_connections.logger"
    )

    # Ensure a clean session state by logging out any pre-existing user.
    client.post("/api/logout")

    # Act: Create a test client. This automatically triggers the 'connect' event.
    test_ws_client = socketio.test_client(app, flask_test_client=client)

    # Assert: The connection is established and logged
    assert test_ws_client.is_connected()

    # Find the call to logger.info and assert its content starts with the expected prefix.
    # This is more robust than matching the exact string with a dynamic SID.
    connect_log_found = any(
        call.args[0].startswith("🟢 Anonymous client connected:")
        for call in mock_logger.info.call_args_list
    )
    assert (
        connect_log_found
    ), "Expected log for anonymous client connection not found."

    # Act: Explicitly disconnect the client
    test_ws_client.disconnect()

    # Assert: The connection is closed and logged
    assert not test_ws_client.is_connected()
    disconnect_log_found = any(
        call.args[0].startswith("🔴 Client disconnected:")
        for call in mock_logger.info.call_args_list
    )
    assert (
        disconnect_log_found
    ), "Expected log for client disconnection not found."


def test_authenticated_websocket_connection_lifecycle(
    app, client, seeded_user, mocker
):
    """
    GIVEN a user who is logged in via a standard HTTP request
    WHEN a WebSocket client connects using that session
    THEN the server should identify the user, log the authenticated connection,
         and assign them to a user-specific room.
    """
    # Arrange: Spy on the logger and join_room function
    mock_logger = mocker.patch(
        "managers.socket_manager.socket_connections.logger"
    )
    mock_join_room = mocker.patch(
        "managers.socket_manager.socket_connections.join_room"
    )

    # 1. Log in the user via a standard POST request to establish a session
    login_response = client.post(
        "/api/login",
        data=json.dumps({"username": "testuser", "password": "password"}),
        content_type="application/json",
    )
    assert login_response.status_code == 200

    # 2. Act: Create a WebSocket test client. It will use the session cookie
    # from the flask_test_client (`client`) to authenticate.
    test_ws_client = socketio.test_client(app, flask_test_client=client)

    # Assert: The connection is established and correctly authenticated
    assert test_ws_client.is_connected()

    # Verify the log message for an authenticated connection.
    auth_connect_log_found = any(
        "User: testuser, Room: testuser" in call.args[0]
        and call.args[0].startswith("🟢 Client connected:")
        for call in mock_logger.info.call_args_list
    )
    assert (
        auth_connect_log_found
    ), "Expected log for authenticated client connection not found."
    mock_join_room.assert_called_once_with("testuser")

    # Cleanup
    test_ws_client.disconnect()
