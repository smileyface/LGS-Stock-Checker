def test_websocket_connection_lifecycle(websocket_client_factory):
    """
    GIVEN a client (anonymous or authenticated)
    WHEN the client establishes and then closes a WebSocket connection
    THEN the server should log the connection and disconnection
    events correctly.
    """
    # Arrange: Unpack the resources provided by the factory fixture
    client_type, ws_client = websocket_client_factory[:2]
    mock_logger, mock_join_room = websocket_client_factory[2:]

    # Assert: The connection is established and logged
    assert ws_client.is_connected()
    mock_logger.info.assert_called_once()
    log_message = mock_logger.info.call_args[0][0]

    # Assert connection behavior based on client type
    if client_type == "authenticated":
        assert log_message.startswith("🟢 Client connected:")
        assert "User: testuser" in log_message
        assert "Room: testuser" in log_message
        mock_join_room.assert_called_once_with("testuser")
    else:  # anonymous
        assert log_message.startswith("🟢 Anonymous client connected:")
        mock_join_room.assert_not_called()

    # Reset mock history before the next action
    mock_logger.reset_mock()

    # Act: Explicitly disconnect the client
    ws_client.disconnect()

    # Assert: The connection is closed and logged
    assert not ws_client.is_connected()
    mock_logger.info.assert_called_once()
    assert mock_logger.info.call_args[0][0].startswith(
        "🔴 Client disconnected:"
    ), "Log message for client disconnection is incorrect."
