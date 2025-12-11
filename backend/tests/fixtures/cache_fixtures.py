import pytest
import json


@pytest.fixture()
def mock_cache_write(mocker, fake_redis):
    """
    Mocks the cache_write function used in socket handlers.
    Stores data in the fake_redis instance so it can be read later in tests.
    """
    def save_data_side_effect(key, value, ex=None):
        print(f"MOCK CACHE WRITE: key='{key}', value='{value}'")
        fake_redis.set(key, json.dumps(value), ex=ex)

    mock = mocker.patch("data.cache.cache_manager.save_data")
    mock.side_effect = save_data_side_effect
    return mock


@pytest.fixture()
def mock_cache_read(mocker, fake_redis):
    """
    Mocks the cache_read function used in socket handlers.
    Reads from the fake_redis instance populated by mock_cache_write.
    """
    def load_data_side_effect(key):
        value_bytes = fake_redis.get(key)
        print(f"MOCK CACHE READ: key='{key}', returning='{value_bytes}'")
        if value_bytes:
            return json.loads(value_bytes)
        return None

    mock = mocker.patch("data.cache.cache_manager.load_data")
    mock.side_effect = load_data_side_effect
    return mock
