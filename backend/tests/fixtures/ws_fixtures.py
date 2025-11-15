import pytest
import json


@pytest.fixture(params=["anonymous", "authenticated"])
def websocket_client_factory(request, app, seeded_user, mocker):
    """
    A parameterized fixture that yields a connected WebSocket test client.

    This factory handles the setup for both anonymous and authenticated
    sessions based on the test's parameterization.

    Yields:
        A tuple containing:
        - (str): The type of client ('anonymous' or 'authenticated').
        - (SocketIOTestClient): The connected WebSocket test client.
        - (MagicMock): The mock for the logger.
        - (MagicMock): The mock for `join_room`.
    """
    # 1. Arrange: Set up mocks
    mock_logger = mocker.patch("managers.socket_manager."
                               "socket_connections.logger")
    mock_join_room = mocker.patch("managers.socket_manager."
                                  "socket_connections.join_room")

    # Import socketio locally to ensure a clean instance for each test run.
    from managers.socket_manager import socketio

    # 2. Arrange: Create the appropriate Flask client and log in if needed
    flask_client = app.test_client()
    if request.param == "authenticated":
        with flask_client:
            login_response = flask_client.post(
                "/api/login",
                data=json.dumps({"username": "testuser",
                                 "password": "password"}),
                content_type="application/json",
            )
            assert login_response.status_code == 200

    # Reset mock history right before the connection to ensure
    # clean assertions.
    mock_logger.reset_mock()

    # 3. Act: Create and connect the WebSocket client
    ws_client = socketio.test_client(app, flask_test_client=flask_client)

    # 4. Yield control to the test function
    yield request.param, ws_client, mock_logger, mock_join_room

    # 5. Teardown: Disconnect the client after the test is done
    if ws_client.is_connected():
        ws_client.disconnect()
