import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash

from data.database.models.orm_models import (
    Base,
    User,
    Store,
    Card,
    Set,
    Finish,
    CardPrinting,
    CardSpecification,
    UserTrackedCards,
)

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_session():
    """Provides a clean, isolated database session for each test function."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session_instance = Session()
    try:
        yield session_instance
    finally:
        session_instance.close()
        Base.metadata.drop_all(bind=engine)


def seed_user(db_session):
    """Helper function to create and commit a test user."""
    user = User(
        username="testuser", password_hash=generate_password_hash("password")
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture(scope="function")
def seeded_user(db_session):
    """Fixture that provides a seeded user, for tests that need one."""
    return seed_user(db_session)


@pytest.fixture
def seeded_user_with_stores(db_session, seeded_user, seeded_stores):
    """Fixture to create a user and associate them with some stores."""
    user = db_session.query(User).filter_by(
        username=seeded_user.username).one()
    user.selected_stores.extend(seeded_stores)
    db_session.commit()
    return user


def seed_stores(db_session):
    """Helper function to create and commit multiple test stores."""
    stores_data = [
        Store(
            name="Test Store",
            slug="test_store",
            homepage="https://test.com",
            search_url="https://test.com/search",
            fetch_strategy="default",
        ),
        Store(
            name="Another Store",
            slug="another_store",
            homepage="https://another.com",
            search_url="https://another.com/search",
            fetch_strategy="default",
        ),
    ]
    db_session.add_all(stores_data)
    db_session.commit()
    return stores_data


@pytest.fixture
def seeded_stores(db_session):
    """Fixture that provides seeded stores, for tests that need them."""
    return seed_stores(db_session)


@pytest.fixture
def seeded_store(seeded_stores):
    """
    Fixture to provide a single test store from the list of seeded stores.
    """
    return next(s for s in seeded_stores if s.slug == "test_store")


@pytest.fixture
def seeded_card_catalogue(db_session):
    db_session.add_all(
        [
            Card(name="Sol Ring"),
            Card(name="Thoughtseize"),
            Card(name="Ugin, the Spirit Dragon"),
            Card(name="Lightning Bolt"),
            Card(name="Counterspell"),
            Card(name="Brainstorm"),
            Card(name="Lurrus of the Dream-Den"),
            Card(name="Swords to Plowshares"),
        ]
    )


@pytest.fixture
def seeded_printings(db_session):
    """Fixture to create a card with multiple printings and finishes."""
    db_session.add_all(
        [
            Card(name="Sol Ring"),
            Card(name="Thoughtseize"),
            Card(name="Ugin, the Spirit Dragon"),
            Set(code="C21", name="Commander 2021"),
            Set(
                code="LTC",
                name="The Lord of the Rings: Tales of Middle-earth Commander",
            ),
            Set(code="ONE", name="Phyrexia: All Will Be One"),
            Set(code="MH2", name="Modern Horizons 2"),
            Set(code="2XM", name="Double Masters"),
            Set(code="M21", name="Core Set 2021"),
            Finish(name="non-foil"),
            Finish(name="foil"),
            Finish(name="etched"),
        ]
    )
    db_session.commit()

    printings_data = [
        ("Sol Ring", "C21", "125", ["non-foil", "foil"]),
        ("Sol Ring", "LTC", "3", ["non-foil", "etched"]),
        ("Sol Ring", "ONE", "254", ["non-foil", "foil"]),
        ("Thoughtseize", "MH2", "107", ["etched"]),
        ("Thoughtseize", "2XM", "107", ["non-foil"]),
        ("Ugin, the Spirit Dragon", "M21", "1", ["foil"]),
    ]

    all_finishes = {f.name: f for f in db_session.query(Finish).all()}

    for card_name, set_code, collector_number, finish_names in printings_data:
        printing = CardPrinting(
            card_name=card_name,
            set_code=set_code,
            collector_number=collector_number,
        )
        printing.available_finishes.extend(
            [all_finishes[name] for name in finish_names]
        )
        db_session.add(printing)

    db_session.commit()


@pytest.fixture
def seeded_user_with_cards(db_session):
    """Fixture to create a user with multiple cards and specifications."""
    user = User(
        username="testuser", password_hash=generate_password_hash("password")
    )

    # Create the unique card names in the 'cards' lookup table first
    db_session.add_all(
        [
            Card(name="Lightning Bolt"),
            Card(name="Counterspell"),
            Card(name="Sol Ring"),
            Card(name="Brainstorm"),
            Card(name="Lurrus of the Dream-Den"),
        ]
    )
    # Commit to ensure these exist before we reference them via foreign key.
    db_session.commit()

    # Create Finish objects to be associated with specifications
    finish_nonfoil = Finish(name="non-foil")
    finish_foil = Finish(name="foil")
    finish_etched = Finish(name="etched")
    db_session.add_all([finish_nonfoil, finish_foil, finish_etched])
    db_session.commit()

    # Create the UserTrackedCards instances
    tracked_card1 = UserTrackedCards(card_name="Lightning Bolt", amount=4)
    tracked_card2 = UserTrackedCards(card_name="Counterspell", amount=2)
    tracked_card3 = UserTrackedCards(card_name="Sol Ring", amount=1)

    # Append specifications directly to the tracked card objects
    tracked_card1.specifications.append(
        CardSpecification(set_code="2ED", finish_id=finish_nonfoil.id)
    )
    tracked_card1.specifications.append(
        CardSpecification(set_code="3ED", finish_id=finish_foil.id)
    )
    tracked_card2.specifications.append(
        CardSpecification(set_code="CMR", finish_id=finish_etched.id)
    )

    # Append the fully-formed tracked cards to the user's collection
    user.cards.append(tracked_card1)
    user.cards.append(tracked_card2)
    user.cards.append(tracked_card3)

    # Add the top-level user object; cascades will handle the rest.
    db_session.add(user)
    db_session.commit()

    # Re-fetch the user to ensure all relationships are fresh and not expired
    # after the commit. This prevents DetachedInstanceError in tests.
    refreshed_user = db_session.query(User).filter_by(
        username=user.username).one()
    return refreshed_user


@pytest.fixture
def multiple_users_with_cards(db_session):
    """Fixture to create multiple users tracking various cards."""
    # Create unique card names
    cards = [
        Card(name="Sol Ring"),
        Card(name="Brainstorm"),
        Card(name="Lurrus of the Dream-Den"),
    ]
    db_session.add_all(cards)
    db_session.commit()

    # User 1 tracks Sol Ring and Brainstorm
    user1 = User(username="user1", password_hash="hash1")
    user1.cards.append(UserTrackedCards(card_name="Sol Ring", amount=1))
    user1.cards.append(UserTrackedCards(card_name="Brainstorm", amount=4))

    # User 2 tracks Sol Ring and Lurrus
    user2 = User(username="user2", password_hash="hash2")
    user2.cards.append(UserTrackedCards(card_name="Sol Ring", amount=1))
    user2.cards.append(
        UserTrackedCards(card_name="Lurrus of the Dream-Den", amount=1)
    )

    # User 3 tracks no cards of interest
    user3 = User(username="user3", password_hash="hash3")

    db_session.add_all([user1, user2, user3])
    db_session.commit()
