import pytest
from unittest.mock import patch, MagicMock
import requests
import gzip
import io
import json

from externals.scryfall_api import (
    fetch_scryfall_card_names,
    fetch_all_card_data,
    CACHE_EXPIRATION_SECONDS,
)

# Define paths for patching
REQUESTS_GET_PATH = "externals.scryfall_api.requests.get"
CACHE_MANAGER_PATH = "externals.scryfall_api.cache_manager"
LOGGER_INFO_PATH = "externals.scryfall_api.logger.info"
LOGGER_ERROR_PATH = "externals.scryfall_api.logger.error"


@pytest.fixture
def mock_cache_manager():
    """Fixture to mock the cache manager."""
    with patch(CACHE_MANAGER_PATH) as mock:
        mock.load_data.return_value = None  # Default to cache miss
        yield mock


@patch(REQUESTS_GET_PATH)
def test_fetch_scryfall_card_names_success(
    mock_requests_get, mock_cache_manager
):
    """
    GIVEN a successful API response for card names
    WHEN fetch_scryfall_card_names is called
    THEN it should return the list of names and cache them.
    """
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": ["card1", "card2"]}
    mock_requests_get.return_value = mock_response

    # Act
    result = fetch_scryfall_card_names()

    # Assert
    assert result == ["card1", "card2"]
    mock_requests_get.assert_called_once_with(
        "https://api.scryfall.com/catalog/card-names"
    )
    mock_cache_manager.save_data.assert_called_once_with(
        "scryfall_card_names", ["card1", "card2"], ex=CACHE_EXPIRATION_SECONDS
    )


def test_fetch_scryfall_card_names_from_cache(mock_cache_manager):
    """
    GIVEN card names are already in the cache
    WHEN fetch_scryfall_card_names is called
    THEN it should return the cached data without making an API call.
    """
    # Arrange
    mock_cache_manager.load_data.return_value = ["cached_card1",
                                                 "cached_card2"]

    with patch(REQUESTS_GET_PATH) as mock_requests_get:
        # Act
        result = fetch_scryfall_card_names()

        # Assert
        assert result == ["cached_card1", "cached_card2"]
        mock_requests_get.assert_not_called()
        mock_cache_manager.load_data.assert_called_once_with(
            "scryfall_card_names"
        )


@patch(REQUESTS_GET_PATH)
@patch(LOGGER_ERROR_PATH)
def test_fetch_scryfall_card_names_api_error(
    mock_logger_error, mock_requests_get, mock_cache_manager
):
    """
    GIVEN the Scryfall API returns an error
    WHEN fetch_scryfall_card_names is called
    THEN it should log the error and return an empty list.
    """
    # Arrange
    mock_requests_get.side_effect = requests.exceptions.RequestException(
        "API is down"
    )

    # Act
    result = fetch_scryfall_card_names()

    # Assert
    assert result == []
    mock_logger_error.assert_called_once()
    assert "Failed to fetch card names" in mock_logger_error.call_args[0][0]


@patch(REQUESTS_GET_PATH)
@patch(LOGGER_ERROR_PATH)
def test_fetch_all_card_data_bulk_uri_missing(
    mock_logger_error, mock_requests_get, mock_cache_manager
):
    """
    GIVEN the bulk data catalog response is missing the 'default_cards' URI
    WHEN fetch_all_card_data is called
    THEN it should log an error and return an empty generator.
    """
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": [{"type": "rulings", "download_uri": "some_uri"}]
    }
    mock_requests_get.return_value = mock_response

    # Act
    result_generator = fetch_all_card_data()

    # Assert
    # Consume the generator and assert that it produces an empty list.
    assert list(result_generator) == []
    mock_logger_error.assert_called_once_with(
        "Could not find 'default_cards' download URI in Scryfall bulk"
        " data response."
    )


@patch(REQUESTS_GET_PATH)
def test_fetch_all_card_data_success(mock_requests_get, mock_cache_manager):
    """
    GIVEN successful responses for bulk data URI and the data file
    WHEN fetch_all_card_data is called
    THEN it should download, decompress, and return the card data.
    """
    # Arrange
    bulk_uri = "http://fake.scryfall.com/all_cards.json.gz"
    mock_bulk_info_resp = MagicMock()
    mock_bulk_info_resp.json.return_value = {
        "data": [{"type": "default_cards", "download_uri": bulk_uri}]
    }

    card_payload = [{"name": "Card A"}, {"name": "Card B"}]
    gzipped_payload = gzip.compress(json.dumps(card_payload).encode("utf-8"))
    mock_card_data_resp = MagicMock()
    mock_card_data_resp.raw = io.BytesIO(
        gzipped_payload
    )  # Use BytesIO for raw stream
    mock_requests_get.side_effect = [mock_bulk_info_resp, mock_card_data_resp]

    # Act
    result_generator = fetch_all_card_data()

    # Assert
    # Consume the generator and assert its contents match the payload.
    assert list(result_generator) == card_payload
    assert mock_requests_get.call_count == 2
    assert (
        mock_requests_get.call_args_list[0].args[0]
        == "https://api.scryfall.com/bulk-data"
    )
    assert mock_requests_get.call_args_list[1].args[0] == bulk_uri
