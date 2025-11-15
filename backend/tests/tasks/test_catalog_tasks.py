import pytest  # noqa
from unittest.mock import patch
from tasks.catalog_tasks import update_card_catalog, update_set_catalog
from datetime import date


@patch("externals.scryfall_api.cache_manager.load_data", return_value=None)
@patch("tasks.catalog_tasks.fetch_scryfall_card_names")
@patch("tasks.catalog_tasks.database")
def test_update_card_catalog_success(
    mock_db, mock_fetch_scryfall_card_names, mock_cache_load
):
    """
    GIVEN a list of card names is successfully fetched
    WHEN update_card_catalog is called
    THEN it should add the new cards to the database.
    """
    # Arrange
    card_names = ["Sol Ring", "Command Tower"]
    mock_fetch_scryfall_card_names.return_value = card_names

    # Act
    update_card_catalog()

    # Assert
    mock_fetch_scryfall_card_names.assert_called_once()
    mock_db.add_card_names_to_catalog.assert_called_once_with(card_names)


@patch("externals.scryfall_api.cache_manager.load_data", return_value=None)
@patch("tasks.catalog_tasks.fetch_scryfall_card_names")
@patch("tasks.catalog_tasks.database")
def test_update_card_catalog_fetch_fails(
    mock_db, mock_fetch_scryfall_card_names, mock_cache_load
):
    """
    GIVEN fetching card names returns nothing (e.g., API is down)
    WHEN update_card_catalog is called
    THEN the database should remain empty.
    """
    # Arrange
    mock_fetch_scryfall_card_names.return_value = None

    # Act
    update_card_catalog()

    # Assert
    mock_fetch_scryfall_card_names.assert_called_once()
    mock_db.add_card_names_to_catalog.assert_not_called()


@patch("externals.scryfall_api.cache_manager.load_data", return_value=None)
@patch("tasks.catalog_tasks.fetch_all_sets")
@patch("tasks.catalog_tasks.database")
def test_update_set_catalog_success(mock_db, mock_fetch_sets, mock_cache_load):
    """
    GIVEN a list of set data is successfully fetched
    WHEN update_set_catalog is called
    THEN it should transform the data and call the database function to add
         the sets.
    """
    # Arrange

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
    mock_db.add_set_data_to_catalog.assert_called_once_with(
        expected_transformed_data
    )


@patch("externals.scryfall_api.cache_manager.load_data", return_value=None)
@patch("tasks.catalog_tasks.fetch_all_sets")
@patch("tasks.catalog_tasks.database")
def test_update_set_catalog_fetch_fails(
    mock_db, mock_fetch_sets, mock_cache_load
):
    """
    GIVEN fetching set data returns nothing
    WHEN update_set_catalog is called
    THEN it should not call the database function.
    """
    # Arrange
    mock_fetch_sets.return_value = None

    # Act
    update_set_catalog()

    # Assert
    mock_fetch_sets.assert_called_once()
    # Ensure the database function is not called when there's no data
    mock_db.add_set_data_to_catalog.assert_not_called()


@patch("externals.scryfall_api.cache_manager.load_data", return_value=None)
@patch("tasks.catalog_tasks.fetch_all_sets")
@patch("tasks.catalog_tasks.database")
def test_update_set_catalog_handles_missing_keys(
    mock_db, mock_fetch_sets, mock_cache_load
):
    """
    GIVEN fetched set data has items with missing keys
    WHEN update_set_catalog is called
    THEN it should filter out the invalid items before calling the database
         function.
    """
    # Arrange
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
    mock_db.add_set_data_to_catalog.assert_called_once_with(expected_call_data)
