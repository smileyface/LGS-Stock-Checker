import pytest  # noqa
import json
from unittest.mock import patch, MagicMock
from tasks.catalog_tasks import (
    update_card_catalog,
    update_set_catalog,
    update_full_catalog,
)
from datetime import date


@patch("tasks.catalog_tasks.fetch_scryfall_card_names")
@patch("managers.redis_manager.redis_manager.get_redis_connection")
def test_update_card_catalog_success(mock_get_redis, mock_fetch):
    """
    GIVEN a list of card names is successfully fetched
    WHEN update_card_catalog is called
    THEN it should publish the card names to the correct Redis channel.
    """
    # Arrange
    mock_redis = MagicMock()
    mock_get_redis.return_value = mock_redis

    card_names = ["Sol Ring", "Command Tower"]
    mock_fetch.return_value = card_names

    # Act
    update_card_catalog()

    # Assert
    mock_fetch.assert_called_once()
    mock_redis.publish.assert_called_once()

    # Verify arguments
    call_args = mock_redis.publish.call_args
    assert call_args[0][0] == "worker-results"

    payload = json.loads(call_args[0][1])
    message_type = payload.pop("type")
    payload = payload["payload"]
    assert message_type == "catalog_card_names_result"
    assert payload == {"names": card_names}


@patch("tasks.catalog_tasks.fetch_scryfall_card_names")
@patch("managers.redis_manager.redis_manager.get_redis_connection")
def test_update_card_catalog_fetch_fails(mock_get_redis, mock_fetch):
    """
    GIVEN fetching card names returns nothing (e.g., API is down)
    WHEN update_card_catalog is called
    THEN it should not publish anything.
    """
    # Arrange
    mock_redis = MagicMock()
    mock_get_redis.return_value = mock_redis
    mock_fetch.return_value = None

    # Act
    update_card_catalog()

    # Assert
    mock_fetch.assert_called_once()
    mock_redis.publish.assert_not_called()


@patch("tasks.catalog_tasks.fetch_all_sets")
@patch("managers.redis_manager.redis_manager.get_redis_connection")
def test_update_set_catalog_success(mock_get_redis, mock_fetch_sets):
    """
    GIVEN a list of set data is successfully fetched
    WHEN update_set_catalog is called
    THEN it should transform the data and publish it to the correct Redis
         channel.
    """
    # Arrange
    mock_redis = MagicMock()
    mock_get_redis.return_value = mock_redis

    raw_set_data = [
        {"code": "M21", "name": "Core Set 2021", "released_at": "2020-06-25"},
        {
            "code": "IKO",
            "name": "Ikoria: Lair of Behemoths",
            "released_at": "2020-04-24",
        },
    ]
    mock_fetch_sets.return_value = raw_set_data

    expected_transformed_data = [
        {
            "code": "M21",
            "name": "Core Set 2021",
            "release_date": date(2020, 6, 25),
        },
        {
            "code": "IKO",
            "name": "Ikoria: Lair of Behemoths",
            "release_date": date(2020, 4, 24),
        },
    ]

    # Act
    update_set_catalog()

    # Assert
    mock_fetch_sets.assert_called_once()
    mock_redis.publish.assert_called_once()

    call_args = mock_redis.publish.call_args
    assert call_args[0][0] == "worker-results"

    payload = json.loads(call_args[0][1])
    message_type = payload.pop("type")
    payload = payload["payload"]
    assert message_type == "catalog_set_data_result"
    expected_sets_json = json.loads(json.dumps(
        expected_transformed_data,
        default=str))
    assert payload == {"sets": expected_sets_json}


@patch("tasks.catalog_tasks.fetch_all_sets")
@patch("managers.redis_manager.redis_manager.get_redis_connection")
def test_update_set_catalog_fetch_fails(mock_get_redis, mock_fetch_sets):
    """
    GIVEN fetching set data returns nothing
    WHEN update_set_catalog is called
    THEN it should not publish anything.
    """
    # Arrange
    mock_redis = MagicMock()
    mock_get_redis.return_value = mock_redis
    mock_fetch_sets.return_value = None

    # Act
    update_set_catalog()

    # Assert
    mock_fetch_sets.assert_called_once()
    mock_redis.publish.assert_not_called()


@patch("tasks.catalog_tasks.fetch_all_sets")
@patch("managers.redis_manager.redis_manager.get_redis_connection")
def test_update_set_catalog_handles_missing_keys(mock_get_redis,
                                                 mock_fetch_sets):
    """
    GIVEN fetched set data has items with missing keys
    WHEN update_set_catalog is called
    THEN it should filter out the invalid items before publishing.
    """
    # Arrange
    mock_redis = MagicMock()
    mock_get_redis.return_value = mock_redis
    raw_set_data = [
        {"code": "M21", "name": "Core Set 2021", "released_at": "2020-06-25"},
        {"name": "Incomplete Set", "released_at": "2020-01-01"},
        {"code": "INV", "released_at": "2000-10-02"},
    ]
    mock_fetch_sets.return_value = raw_set_data

    # Act
    update_set_catalog()

    # Assert
    mock_fetch_sets.assert_called_once()
    # Verify that only the valid item was passed to the database function
    expected_call_data = [
        {
            "code": "M21",
            "name": "Core Set 2021",
            "release_date": date(2020, 6, 25),
        }
    ]
    mock_redis.publish.assert_called_once()
    call_args = mock_redis.publish.call_args
    payload = json.loads(call_args[0][1])
    message_type = payload.pop("type")
    payload = payload["payload"]
    assert message_type == "catalog_set_data_result"
    assert len(payload["sets"]) == 1
    expected_sets_json = json.loads(json.dumps(
        expected_call_data,
        default=str))
    assert payload == {"sets": expected_sets_json}


@patch("tasks.catalog_tasks.fetch_all_card_data")
@patch("managers.redis_manager.redis_manager.get_redis_connection")
@patch("tasks.catalog_tasks.update_card_catalog")
@patch("tasks.catalog_tasks.update_set_catalog")
def test_update_full_catalog_success(
    mock_update_set, mock_update_card, mock_get_redis, mock_fetch_cards
):
    """
    GIVEN a stream of card data is fetched
    WHEN update_full_catalog is called
    THEN it should publish printings and finishes in chunks to Redis.
    """
    # Arrange
    mock_redis = MagicMock()
    mock_get_redis.return_value = mock_redis
    card_stream = [
        {
            "name": "Sol Ring",
            "set": "C21",
            "collector_number": "1",
            "finishes": ["foil", "nonfoil"],
        },
        {
            "name": "Command Tower",
            "set": "C21",
            "collector_number": "2",
            "finishes": ["nonfoil", "etched"],
        },
        {"name": "Incomplete Card"},  # Should be skipped
    ]
    mock_fetch_cards.return_value = card_stream

    # Act
    with patch("tasks.catalog_tasks.CHUNK_SIZE", 2):  # Test chunking
        update_full_catalog()

    # Assert
    mock_update_set.assert_called_once()
    mock_update_card.assert_called_once()
    mock_fetch_cards.assert_called_once()

    # Verify publish calls
    expected_printings_chunk = [
        {
            "card_name": "Sol Ring",
            "set_code": "C21",
            "collector_number": "1",
            "finishes": ["foil", "nonfoil"],
        },
        {
            "card_name": "Command Tower",
            "set_code": "C21",
            "collector_number": "2",
            "finishes": ["nonfoil", "etched"],
        },
    ]
    expected_finishes = ["foil", "nonfoil", "etched"]

    #    expected_calls = [
    #        call(
    #            "catalog_printings_chunk_result",
    #            {"printings": expected_printings_chunk},
    #        ),
    #        call(
    #            "catalog_finishes_chunk_result",
    #            {"finishes": sorted(expected_finishes)},
    #        ),
    #    ]
    # Use any_order because the final finishes chunk could be processed
    # before the printings chunk in some async scenarios, though not here.
    # Sorting the list of finishes ensures the test is deterministic.
    # We need to sort the actual call's list as well.
    # A bit complex to check, so let's check call count
    # and contents separately.

    assert mock_redis.publish.call_count == 2

    # Check printings call
    # We iterate through calls to find the printings chunk
    calls = mock_redis.publish.call_args_list
    printings_payload = None
    finishes_payload = None

    for call_args in calls:
        data = json.loads(call_args[0][1])
        inner_payload = data.get("payload", {})
        if "printings" in inner_payload:
            printings_payload = inner_payload
        elif "finishes" in inner_payload:
            finishes_payload = inner_payload

    assert printings_payload is not None
    assert printings_payload["printings"] == expected_printings_chunk

    assert finishes_payload is not None
    assert sorted(finishes_payload["finishes"]) == sorted(expected_finishes)
