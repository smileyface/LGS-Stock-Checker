import pytest  # noqa
from unittest.mock import MagicMock, patch
from managers.availability_manager.availability_manager import (
    check_availability,
    fetch_availability,
)
from data.database.models.orm_models import UserTrackedCards
from schema.messaging.messages import AvailabilityRequestCommand


@patch(
    "managers.availability_manager.availability_manager."
    "redis_manager.publish_pubsub"
)
def test_check_availability(mock_publish_pubsub):
    """
    Verifies check_availability publishes a command to the scheduler.
    """
    # Arrange
    username = "testuser"

    # Act
    result = check_availability(username)

    # Assert
    mock_publish_pubsub.assert_called_once()
    args, _ = mock_publish_pubsub.call_args
    assert isinstance(args[0], AvailabilityRequestCommand)
    assert args[0].channel == "scheduler-requests"
    assert args[0].payload.user.username == username
    assert result == {
        "status": "requested",
        "message": "Availability update has been requested.",
    }


@patch("managers.availability_manager.availability_manager."
       "redis_manager.publish_pubsub")
@patch("managers.availability_manager."
       "availability_manager.availability_storage")
def test_get_card_availability_with_cached_data(
    mock_storage,
    mock_publish_pubsub,
    db_session,
    user_factory,
    store_factory,
    printing_factory
):
    """
    GIVEN a user tracks 'Sol Ring' and the data IS currently in the cache
    WHEN availability is checked
    THEN the cached data should be returned immediately
    AND NO background fetch task should be queued.
    """
    # -------------------------------------------------------------------------
    # 1. Arrange: Create Real DB State
    # -------------------------------------------------------------------------
    printing_factory(card_name="Sol Ring")
    store = store_factory(name="Test Store", slug="test_store")
    user = user_factory(username="cached_user")

    # Link User -> Store
    user.selected_stores.append(store)
    # Link User -> Card
    user.cards.append(UserTrackedCards(card_name="Sol Ring", amount=1))
    db_session.commit()

    # -------------------------------------------------------------------------
    # 2. Arrange: Mock the Cache Hit
    # -------------------------------------------------------------------------
    cached_items = [
        {"name": "Sol Ring",
         "price": 5.00,
         "condition": "NM",
         "url": "http://.."}
    ]
    # The manager calls this with (store_slug, card_name)
    mock_storage.get_cached_availability_data.return_value = cached_items

    # -------------------------------------------------------------------------
    # 3. Act
    # -------------------------------------------------------------------------
    results = fetch_availability("cached_user")

    # -------------------------------------------------------------------------
    # 4. Assert
    # -------------------------------------------------------------------------
    # Verify the structure matches {store_slug: {card_name: [items]}}
    assert "test_store" in results
    assert "Sol Ring" in results["test_store"]
    assert results["test_store"]["Sol Ring"] == cached_items

    # CRITICAL: Verify we did NOT trigger a background scrape
    mock_publish_pubsub.assert_not_called()


@patch("managers.availability_manager.availability_manager."
       "redis_manager.publish_pubsub")
@patch("managers.availability_manager.availability_manager."
       "availability_storage")
def test_get_card_availability_with_no_cached_data(
    mock_storage,
    mock_publish_pubsub,
    db_session,
    user_factory,
    store_factory,
    printing_factory
):
    """
    GIVEN a user tracking 'Sol Ring' at 'Test Store' (Real DB Data)
    AND no data in the cache (Mocked Redis)
    WHEN availability is checked
    THEN a fetch task should be queued.
    """
    # -------------------------------------------------------------------------
    # 1. Arrange: Use Factories to create a valid Database State
    # -------------------------------------------------------------------------

    # Create the Catalog Entry
    # This ensures 'Sol Ring' exists as a valid card in the system
    printing_factory(card_name="Sol Ring", set_code="C21",
                     finishes=["non-foil"])

    # Create the Store
    store = store_factory(name="Test Store", slug="test_store")

    # Create the User
    user = user_factory(username="real_user")

    # Link User -> Store (User Preferences)
    # We must re-query or use the objects attached to the session
    user.selected_stores.append(store)

    # Link User -> Card (Tracked Cards)
    # We add a tracked card directly to the user
    tracked_card = UserTrackedCards(card_name="Sol Ring", amount=1)
    user.cards.append(tracked_card)

    db_session.commit()

    # Configure the Mock for Cache Miss
    mock_storage.get_cached_availability_data.return_value = None

    # -------------------------------------------------------------------------
    # 2. Act
    # -------------------------------------------------------------------------
    # We pass the username of the user we just created in the DB
    results = fetch_availability("real_user")

    # -------------------------------------------------------------------------
    # 3. Assert
    # -------------------------------------------------------------------------
    # Should be empty because cache was empty
    assert results == {}

    # Verify the background task was triggered
    assert mock_publish_pubsub.called

    # Optional: Dig deeper to ensure the payload was correct
    # This confirms the Manager correctly read "Sol Ring" and "test_store"
    #  from the DB
    args, _ = mock_publish_pubsub.call_args
    message = args[0]
    # Assuming the message payload structure:
    assert message.payload.store.slug == "test_store"
    assert message.payload.card_data.card.name == "Sol Ring"


@patch("managers.availability_manager.availability_manager."
       "redis_manager.publish_pubsub")
@patch("managers.availability_manager.availability_manager."
       "availability_storage")
@patch("managers.availability_manager.availability_manager."
       "user_manager.get_user_stores")
def test_get_card_availability_handles_invalid_store(
    mock_get_user_stores,
    mock_storage,
    mock_publish_pubsub,
    db_session,
    user_factory,
    store_factory,
    printing_factory
):
    """
    Verifies that stores with no slug (or None objects) are skipped gracefully,
    while valid stores are processed.
    """
    # -------------------------------------------------------------------------
    # 1. Arrange: Create Valid Data using Factories
    # -------------------------------------------------------------------------
    # Ensure "Sol Ring" exists in the catalog
    printing_factory(card_name="Sol Ring")

    # Create a REAL store and user
    valid_store = store_factory(name="Valid Store", slug="valid-store")
    user = user_factory(username="testuser")

    # Add a tracked card so 'load_card_list' (which runs for real)
    #  finds something
    user.cards.append(UserTrackedCards(card_name="Sol Ring", amount=1))
    db_session.commit()

    # -------------------------------------------------------------------------
    # 2. Arrange: Inject Invalid Data via Mock
    # -------------------------------------------------------------------------
    # Since the DB won't let us save a Store with slug=None,
    #  we mock the retrieval
    # to return a list containing: [Real Store, None, Bad Mock Store]

    mock_bad_store = MagicMock()
    mock_bad_store.slug = None  # Simulates a broken object
    mock_bad_store.name = "Broken Store"

    mock_get_user_stores.return_value = [
        valid_store,       # The real SQLAlchemy object we created
        None,              # A None value (should be skipped)
        mock_bad_store     # A store with no slug (should be skipped)
    ]

    # -------------------------------------------------------------------------
    # 3. Act
    # -------------------------------------------------------------------------
    fetch_availability("testuser")

    # -------------------------------------------------------------------------
    # 4. Assert
    # -------------------------------------------------------------------------
    # Verify logic: The manager should have called storage ONLY
    #  for 'valid-store'
    mock_storage.get_cached_availability_data.assert_called_once_with(
        "valid-store", "Sol Ring"
    )
