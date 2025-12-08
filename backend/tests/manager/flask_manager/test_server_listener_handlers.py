from unittest.mock import patch
from managers import availability_manager
from managers.flask_manager.server_listener import (
    _handle_availability_result,
    _handle_catalog_card_names_result,
    _handle_catalog_set_data_result,
    _handle_catalog_finishes_result,
    _handle_catalog_printings_chunk_result
)
from data.database.models.orm_models import Card, Set


# This is now an integration test and doesn't need mocks for the cache.
def test_handle_availability_result():
    """
    GIVEN an availability result payload
    WHEN _handle_availability_result is called
    THEN it should write the data to the cache, which can then be retrieved.
    """
    # Arrange
    mock_result = {
        "store": "TestStore",
        "card": "Sol Ring",
        "items": [{"price": 9.99, "stock": 5}],
    }

    # Act
    _handle_availability_result(mock_result)

    # Assert: Verify by reading from the cache, not by checking a mock.
    cached_data = availability_manager.get_cached_availability_data(
        "TestStore", "Sol Ring"
    )
    assert cached_data == [{"price": 9.99, "stock": 5}]


@patch("managers.flask_manager.server_listener"
       ".database.add_card_names_to_catalog")
def test_handle_catalog_card_names_result(mock_add_names):
    """
    GIVEN a payload with card names
    WHEN _handle_catalog_card_names_result is called
    THEN it should call the database function to add the names.
    """
    # Arrange
    mock_payload = {"names": ["Sol Ring", "Brainstorm"]}

    # Act
    _handle_catalog_card_names_result(mock_payload)

    # Assert
    mock_add_names.assert_called_once_with(["Sol Ring", "Brainstorm"])


@patch("managers.flask_manager.server_listener"
       ".database.add_set_data_to_catalog")
def test_handle_catalog_set_data_result(mock_add_sets):
    """
    GIVEN a payload with set data
    WHEN _handle_catalog_set_data_result is called
    THEN it should call the database function to add the sets.
    """
    # Arrange
    mock_payload = {"sets": [{"code": "M21", "name": "Core Set 2021"}]}

    # Act
    _handle_catalog_set_data_result(mock_payload)

    # Assert
    mock_add_sets.assert_called_once_with(
        [{"code": "M21", "name": "Core Set 2021"}]
    )


@patch("managers.flask_manager.server_listener"
       ".database.bulk_add_finishes")
def test_handle_catalog_finishes_result(mock_add_finishes):
    """
    GIVEN a payload with finishes
    WHEN _handle_catalog_finishes_result is called
    THEN it should call the database function to add the finishes.
    """
    # Arrange
    mock_payload = {"finishes": ["foil", "non-foil"]}

    # Act
    _handle_catalog_finishes_result(mock_payload)

    # Assert
    mock_add_finishes.assert_called_once_with(["foil", "non-foil"])


@patch("managers.flask_manager.server_listener."
       "database.bulk_add_printing_finish_associations")
@patch("managers.flask_manager.server_listener."
       "database.get_chunk_finish_ids")
@patch("managers.flask_manager.server_listener."
       "database.get_chunk_printing_ids")
@patch("managers.flask_manager.server_listener."
       "database.bulk_add_card_printings")
def test_handle_catalog_printings_chunk_result(
    mock_add_printings, mock_get_ids, mock_get_finishes, mock_add_associations
):
    """
    GIVEN a payload with a chunk of card printings
    WHEN _handle_catalog_printings_chunk_result is called
    THEN it should call the correct database functions in sequence.
    """
    # Arrange
    mock_payload = {
        "printings": [
            {
                "card_name": "Sol Ring", "set_code": "C21",
                "collector_number": "125", "finishes": ["non-foil", "foil"]
            }
        ]
    }
    # Mock the return values for the lookup functions
    mock_get_ids.return_value = {("Sol Ring", "C21", "125"): 1}
    mock_get_finishes.return_value = {"non-foil": 1, "foil": 2}

    # Act
    _handle_catalog_printings_chunk_result(mock_payload)

    # Assert
    mock_add_printings.assert_called_once_with([
        {
            "card_name": "Sol Ring", "set_code": "C21",
            "collector_number": "125"
        }
    ])
    mock_get_ids.assert_called_once_with(mock_payload["printings"])
    mock_get_finishes.assert_called_once()
    mock_add_associations.assert_called_once_with([
        {"printing_id": 1, "finish_id": 1},
        {"printing_id": 1, "finish_id": 2}
    ])


# --- Integration Tests ---


def test_integration_handle_catalog_card_names_result(db_session):
    """
    GIVEN a payload with new card names
    WHEN the handler is called without mocking the database
    THEN the new card names should be committed to the database.
    """
    # Arrange
    payload = {"names": ["New Card One", "New Card Two"]}

    # Act
    _handle_catalog_card_names_result(payload)

    # Assert
    cards = db_session.query(Card).filter(Card
                                          .name
                                          .in_(payload["names"])).all()
    assert len(cards) == 2
    assert {card.name for card in cards} == {"New Card One", "New Card Two"}


def test_integration_handle_catalog_set_data_result(db_session):
    """
    GIVEN a payload with new set data
    WHEN the handler is called without mocking the database
    THEN the new sets should be committed to the database.
    """
    # Arrange
    payload = {"sets": [{"code": "NEW", "name": "A New Set"}]}

    # Act
    _handle_catalog_set_data_result(payload)

    # Assert
    new_set = db_session.query(Set).filter_by(code="NEW").one_or_none()
    assert new_set is not None
    assert new_set.name == "A New Set"
