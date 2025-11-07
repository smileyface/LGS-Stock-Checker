"""
Unit tests for the store manager and dynamic store loading mechanism.
"""
import importlib
from unittest.mock import MagicMock, patch

from LGS_Stock_Backend.managers.store_manager.stores.storefronts.crystal_commerce_store import CrystalCommerceStore
from LGS_Stock_Backend.managers.store_manager.stores.game_kastle_santa_clara import Game_Kastle_Santa_Clara


@patch('LGS_Stock_Backend.data.database')
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
    mock_store_1.fetch_strategy = "crystal_commerce"

    mock_store_2 = MagicMock()
    mock_store_2.name = "Game Kastle (Santa Clara)"
    mock_store_2.slug = "game_kastle_santa_clara"
    mock_store_2.homepage = "https://gamekastle.co/"
    mock_store_2.fetch_strategy = "default"

    mock_database.get_all_stores.return_value = [mock_store_1, mock_store_2]

    # --- Act ---
    # We need to reload the module to trigger the dynamic loading logic again
    from LGS_Stock_Backend.managers.store_manager import stores
    importlib.reload(stores)
    STORE_REGISTRY = stores.STORE_REGISTRY

    # --- Assert ---
    assert len(STORE_REGISTRY) == 2
    assert isinstance(STORE_REGISTRY["authority_games_mesa_az"], CrystalCommerceStore)
    assert isinstance(STORE_REGISTRY["game_kastle_santa_clara"], Game_Kastle_Santa_Clara)
    assert STORE_REGISTRY["authority_games_mesa_az"].name == "Authority Games (Mesa, AZ)"