import pytest
from unittest.mock import MagicMock


# Mock Card class to simulate the structure of card objects from user_manager
class MockCard:
    def __init__(self, name):
        self.name = name

    def model_dump(self):
        """Simulates Pydantic's model_dump for task queuing."""
        return {"name": self.name}


# Mocking UserTrackedCardSchema
class MockUserTrackedCard:
    def __init__(self, card: MockCard, amount, specifications):
        self.card = card
        self.amount = amount
        self.specifications = specifications

    def model_dump(self):
        """Simulates Pydantic's model_dump for task queuing."""
        return {
            "card": self.card.model_dump(),
            "amount": self.amount,
            "specifications": [
                {
                    "set_code": spec.get("set_code"),
                    "collector_number": spec.get("collector_number"),
                    "finish": spec.get("finish"),
                }
                for spec in self.specifications
            ],
        }


class MockCardAvailabilityData:
    def __init__(self, price: str = "0.00"):
        self.price = price

    def model_dump(self):
        """Simulates Pydantic's model_dump for cached data."""
        return {"price": self.price}

# Global variable to hold the mock Redis instance, accessible by fixtures.
_global_mock_redis_instance = None


def set_global_mock_redis_instance(instance):
    """Sets the global mock redis instance."""
    global _global_mock_redis_instance
    _global_mock_redis_instance = instance


@pytest.fixture(autouse=True)
def mock_redis_manager_objects(mocker):
    """
    Automatically mock the low-level Redis connection objects and the
    import-time Queue/Scheduler objects to prevent any real network calls.
    """
    global _global_mock_redis_instance

    mocker.patch(
        "managers.redis_manager.redis_manager.get_redis_connection",
        _global_mock_redis_instance,
    )

    mock_queue = MagicMock()
    mock_queue.task.side_effect = lambda func: func
    mocker.patch("managers.redis_manager.redis_manager.queue", mock_queue)
    mocker.patch("managers.redis_manager.redis_manager.scheduler", MagicMock())


@pytest.fixture(autouse=True)
def mock_db_session_for_app(mocker, db_session):
    """
    Automatically mocks the application's session provider to return the
    test-specific db_session. This ensures that application code
    (e.g., in route handlers) uses the same isolated database session as the
    test fixtures.
    """
    mocker.patch(
        "data.database.session_manager.get_session", return_value=db_session
    )


@pytest.fixture(autouse=True)
def mock_fetch_sets(mocker):
    """Mocks the fetch_all_sets function."""
    mock = mocker.patch("externals.scryfall_api.fetch_all_sets")
    mock.return_value = []
    return mock


@pytest.fixture(autouse=True)
def mock_fetch_all_card_data(mocker):
    """
    Mocks the fetch_all_card_data function to prevent large network calls.
    """
    mock = mocker.patch("externals.scryfall_api.fetch_all_card_data")
    mock.return_value = []
    return mock


@pytest.fixture
def mock_cache_availability(mocker):
    """
    Mocks the cache_availability function used in socket handlers.
    """
    return mocker.patch("managers.availability_manager."
                        "cache_availability_data")
