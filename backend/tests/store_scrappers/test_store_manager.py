"""
Unit tests for the store manager and dynamic store loading mechanism.
"""

import importlib
from unittest.mock import MagicMock, patch


@patch("data.database")
def test_store_registry_loads_from_db(mock_database):
    """
    GIVEN a mock database that returns store data
    WHEN the store registry module is imported (or reloaded)
    THEN the STORE_REGISTRY should be populated with the correct store instances.
    """
    # --- Arrange ---
    # Create mock ORM objects that simulate what SQLAlchemy would return
    mock_store_1 = MagicMock()
    mock_store_1.name = "Authority Games (Mesa, AZ)"
    mock_store_1.slug = "authority_games_mesa_az"
    mock_store_1.homepage = "https://authoritygames.crystalcommerce.com/"
    mock_store_1.search_url = (
        "https://authoritygames.crystalcommerce.com/products/search"
    )
    mock_store_1.fetch_strategy = "crystal_commerce"

    mock_database.get_all_stores.return_value = [mock_store_1]

    # --- Act ---
    # We need to reload the module to trigger the dynamic loading logic again
    from managers.store_manager import stores
    from managers.store_manager.stores.storefronts.crystal_commerce_store import (
        CrystalCommerceStore,
        _make_request_with_retries,
    )

    importlib.reload(stores)
    STORE_REGISTRY = stores.STORE_REGISTRY

    # Access the underlying registry to test
    registry = STORE_REGISTRY.get_registry()

    # --- Assert ---
    assert len(registry) == 1
    assert "authority_games_mesa_az" in registry
    assert isinstance(registry["authority_games_mesa_az"], CrystalCommerceStore)
    assert (
        registry["authority_games_mesa_az"].name == "Authority Games (Mesa, AZ)"
    )
