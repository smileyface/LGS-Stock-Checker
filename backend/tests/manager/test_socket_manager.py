from unittest.mock import MagicMock

# Import the function to be tested and its dependencies
from managers.socket_manager.socket_emit import emit_from_worker, REDIS_URL


def test_emit_from_worker(mocker):
    """
    GIVEN an event name, data payload, and a room name
    WHEN the emit_from_worker function is called
    THEN it should initialize a new SocketIO instance with the correct Redis message queue
    AND call the 'emit' method on that instance with the correct arguments.
    """
    # Arrange
    # We patch the `SocketIO` class where it is looked up, which is inside the `socket_emit` module.
    mock_socketio_class = mocker.patch(
        "managers.socket_manager.socket_emit.SocketIO"
    )

    # The constructor of SocketIO returns an instance, so we create a mock for that instance.
    mock_socketio_instance = MagicMock()
    mock_socketio_class.return_value = mock_socketio_instance

    test_event = "test_worker_event"
    test_data = {"message": "hello from worker"}
    test_room = "user123"

    # Act
    emit_from_worker(test_event, test_data, test_room)

    # Assert
    # 1. Verify that a new SocketIO instance was created with the message_queue pointing to our Redis URL.
    mock_socketio_class.assert_called_once_with(message_queue=REDIS_URL)

    # 2. Verify that the `emit` method on this new instance was called with the correct parameters.
    mock_socketio_instance.emit.assert_called_once_with(
        test_event, test_data, room=test_room
    )
