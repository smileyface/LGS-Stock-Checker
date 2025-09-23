import pytest
from tasks.catalog_tasks import update_card_catalog, update_set_catalog
from data.database.models import Card, Set

 
def test_update_card_catalog_success(mock_fetch_scryfall_card_names, db_session):
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
    cards_in_db = db_session.query(Card).all()
    assert {c.name for c in cards_in_db} == {"Sol Ring", "Command Tower"}


def test_update_card_catalog_fetch_fails(mock_fetch_scryfall_card_names, db_session):
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
    cards_in_db = db_session.query(Card).count()
    assert cards_in_db == 0


def test_update_set_catalog_success(mock_fetch_sets, db_session):
    """
    GIVEN a list of set data is successfully fetched
    WHEN update_set_catalog is called
    THEN it should transform the data and call the database function to add the sets.
    """
    # Arrange

    raw_set_data = [
        {"code": "M21", "name": "Core Set 2021", "released_at": "2020-06-25"},
        {"code": "IKO", "name": "Ikoria: Lair of Behemoths", "released_at": "2020-04-24"},
    ]
    mock_fetch_sets.return_value = raw_set_data


    expected_transformed_data = [
        {"code": "M21", "name": "Core Set 2021", "release_date": "2020-06-25"},
        {"code": "IKO", "name": "Ikoria: Lair of Behemoths", "release_date": "2020-04-24"},
    ]


    # Act
    update_set_catalog()

    # Assert
    mock_fetch_sets.assert_called_once()
    sets_in_db = db_session.query(Set).all()
    assert len(sets_in_db) == 2
    set_codes_in_db = {s.code for s in sets_in_db}
    assert set_codes_in_db == {"M21", "IKO"}


def test_update_set_catalog_fetch_fails(mock_fetch_sets, db_session):
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
    sets_in_db = db_session.query(Set).count()
    assert sets_in_db == 0


def test_update_set_catalog_handles_missing_keys(mock_fetch_sets, db_session):
    """
    GIVEN fetched set data has items with missing keys
    WHEN update_set_catalog is called
    THEN it should filter out the invalid items before calling the database function.
    """
    # Arrange
    raw_set_data = [

        {"code": "M21", "name": "Core Set 2021", "released_at": "2020-06-25"},
        {"name": "Incomplete Set", "released_at": "2020-01-01"},  # Missing code
        {"code": "INV", "released_at": "2000-10-02"},  # Missing name
    ]
    mock_fetch_sets.return_value = raw_set_data

    # Act
    update_set_catalog()

    # Assert
    mock_fetch_sets.assert_called_once()
    sets_in_db = db_session.query(Set).all()
    assert len(sets_in_db) == 1
    assert sets_in_db[0].code == "M21"