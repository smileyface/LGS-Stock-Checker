import data.database as data






def test_get_store_metadata(seeded_store):
    """
    GIVEN a store exists in the database
    WHEN get_store_metadata is called with the store's slug
    THEN the correct store object is returned.
    """
    # Act
    store = data.get_store_metadata("test_store")

    # Assert
    assert store is not None
    assert store.name == "Test Store"


def test_get_store_metadata_not_found(db_session):
    """
    GIVEN a store slug that does not exist in the database
    WHEN get_store_metadata is called with that slug
    THEN None is returned.
    """
    # Act
    store = data.get_store_metadata("non_existent_store")

    # Assert
    assert store is None


def test_get_all_stores(seeded_stores):
    """
    GIVEN multiple stores exist in the database
    WHEN get_all_stores is called
    THEN a list containing all store objects is returned.
    """
    # Act
    stores = data.get_all_stores()

    # Assert
    assert len(stores) == len(seeded_stores)
    retrieved_slugs = {s.slug for s in stores}
    expected_slugs = {s.slug for s in seeded_stores}
    assert retrieved_slugs == expected_slugs


def test_get_all_stores_empty(db_session):
    """
    GIVEN the database contains no stores
    WHEN get_all_stores is called
    THEN an empty list is returned.
    """
    # Act
    stores = data.get_all_stores()

    # Assert
    assert stores == []