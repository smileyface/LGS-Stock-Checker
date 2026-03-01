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


# -----------------------------------------------------------------------------
# Factories: The intuitive way to generate data on demand
# -----------------------------------------------------------------------------

@pytest.fixture
def user_factory(db_session):
    """
    Returns a function to create a user dynamically.
    Usage: user = user_factory(username="alice", password="secure")
    """
    def _create_user(username="testuser", password="password"):
        user = User(
            username=username,
            password_hash=generate_password_hash(password)
        )
        db_session.add(user)
        db_session.commit()
        return user
    return _create_user


@pytest.fixture
def store_factory(db_session):
    """
    Returns a function to create a store dynamically.
    """
    def _create_store(name="Test Store", slug="test_store", **kwargs):
        store = Store(
            name=name,
            slug=slug,
            homepage=kwargs.get("homepage", f"https://{slug}.com"),
            search_url=kwargs.get("search_url", f"https://{slug}.com/search"),
            fetch_strategy=kwargs.get("fetch_strategy", "default"),
        )
        db_session.add(store)
        db_session.commit()
        return store
    return _create_store


# -----------------------------------------------------------------------------
# Catalog Factories (The New Stuff)
# -----------------------------------------------------------------------------

@pytest.fixture
def card_factory(db_session):
    """
    Creates a Card.
    Usage: card = card_factory(name="Black Lotus")
    """
    def _create_card(name="Test Card"):
        # Check if exists to prevent UniqueConstraint errors
        existing = db_session.query(Card).filter_by(name=name).first()
        if existing:
            return existing

        card = Card(name=name)
        db_session.add(card)
        db_session.commit()
        return card
    return _create_card


@pytest.fixture
def set_factory(db_session):
    """
    Creates a Set.
    Usage: set_obj = set_factory(code="MH2", name="Modern Horizons 2")
    """
    def _create_set(code="TST", name="Test Set"):
        existing = db_session.query(Set).filter_by(code=code).first()
        if existing:
            return existing

        set_obj = Set(code=code, name=name)
        db_session.add(set_obj)
        db_session.commit()
        return set_obj
    return _create_set


@pytest.fixture
def finish_factory(db_session):
    """
    Ensures a Finish exists.
    Usage: foil = finish_factory("foil")
    """
    def _create_finish(name="non-foil"):
        existing = db_session.query(Finish).filter_by(name=name).first()
        if existing:
            return existing

        finish = Finish(name=name)
        db_session.add(finish)
        db_session.commit()
        return finish
    return _create_finish


@pytest.fixture
def printing_factory(db_session, card_factory, set_factory, finish_factory):
    """
    Creates a fully linked CardPrinting.
    This is the 'Master Factory' for catalog data.

    Usage:
        # Simplest:
        p = printing_factory()

        # Custom:
        p = printing_factory(card_name="Sol Ring",
        set_code="C21",
        finishes=["foil"])
    """
    def _create_printing(card_name="Test Card",
                         set_code="TST",
                         collector_number="1",
                         finishes=None):
        if finishes is None:
            finishes = ["non-foil"]

        # 1. Ensure dependencies exist
        card_factory(name=card_name)
        set_factory(code=set_code)
        finish_objs = [finish_factory(name=f) for f in finishes]

        # 2. Create the printing
        printing = CardPrinting(
            card_name=card_name,
            set_code=set_code,
            collector_number=collector_number
        )

        # 3. Link finishes
        printing.available_finishes.extend(finish_objs)

        db_session.add(printing)
        db_session.commit()
        return printing
    return _create_printing


# -----------------------------------------------------------------------------
# Seeding: Standardized datasets for when you just need 'stuff'
# -----------------------------------------------------------------------------

@pytest.fixture
def seeded_user(user_factory):
    """Provides a standard default user (testuser/password)."""
    return user_factory(username="testuser", password="password")


@pytest.fixture
def seeded_stores(store_factory):
    """Provides a standard list of stores."""
    return [
        store_factory(name="Test Store", slug="test_store"),
        store_factory(name="Another Store", slug="another_store"),
    ]


@pytest.fixture
def seeded_user_with_stores(db_session, seeded_user, seeded_stores):
    """Provides a user who has selected the standard stores."""
    # Re-query to ensure attached to current session
    user = db_session.query(User).filter_by(
        username=seeded_user.username).one()
    user.selected_stores.extend(seeded_stores)
    db_session.commit()
    return user


@pytest.fixture
def seeded_catalog(db_session):
    """
    Seeds a comprehensive catalog of Cards, Sets, and Finishes.
    Useful for integration tests requiring a full DB state.
    """
    # 1. Finishes
    finishes = [Finish(name=n) for n in ["non-foil", "foil", "etched"]]
    db_session.add_all(finishes)

    # 2. Sets
    sets = [
        Set(code="C21", name="Commander 2021"),
        Set(code="MH2", name="Modern Horizons 2"),
        Set(code="2XM", name="Double Masters"),
        Set(code="M21", name="Core Set 2021"),
        Set(code="ICE", name="Ice Age"),
    ]
    db_session.add_all(sets)

    # 3. Cards
    cards = [
        Card(name="Sol Ring"),
        Card(name="Thoughtseize"),
        Card(name="Ugin, the Spirit Dragon"),
        Card(name="Brainstorm"),
        Card(name="Lightning Bolt"),
    ]
    db_session.add_all(cards)

    db_session.commit()


@pytest.fixture
def seeded_printings(db_session, seeded_catalog):
    """Seeds specific card printings linking cards, sets, and finishes."""
    # Helper to get finish objects
    finishes = {f.name: f for f in db_session.query(Finish).all()}

    data = [
        ("Sol Ring", "C21", "125", ["non-foil", "foil"]),
        ("Thoughtseize", "MH2", "107", ["etched"]),
        ("Ugin, the Spirit Dragon", "M21", "1", ["foil"]),
        ("Brainstorm", "ICE", "1", ["non-foil"])
    ]

    for card_name, set_code, col_num, finish_names in data:
        printing = CardPrinting(
            card_name=card_name,
            set_code=set_code,
            collector_number=col_num,
        )
        printing.available_finishes.extend([finishes[n] for n in finish_names])
        db_session.add(printing)

    db_session.commit()


@pytest.fixture
def seeded_user_with_cards(db_session, seeded_user, seeded_printings):
    """
    Example of how to manually add complex tracked cards
     using the data we just seeded.
    """
    # NOTE: We can't easily factory-ize UserTrackedCards because it has complex
    # relationships that depend on specific DB IDs. It's usually easier to do
    # this manually in tests or keep this
    # specific fixture for the "standard" scenario.

    # ... (Keep existing implementation for seeded_user_with_cards
    # or refactor similarly)
    # For brevity, preserving the logic from your original file:
    user = db_session.query(User).filter_by(username="testuser").one()

    # Helper to find finish IDs
    finishes = {f.name: f.id for f in db_session.query(Finish).all()}

    # 1. Lightning Bolt (Specific Printing)
    bolt = UserTrackedCards(card_name="Lightning Bolt", amount=4)
    bolt.specifications.append(CardSpecification(set_code="C21",
                                                 collector_number="125",
                                                 finish_id=finishes["non-foil"]
                                                 ))
    bolt.specifications.append(CardSpecification(set_code="LTC",
                                                 collector_number="3",
                                                 finish_id=finishes["foil"]))

    # 2. Sol Ring (Generic)
    sol = UserTrackedCards(card_name="Sol Ring", amount=1)

    # 3. Counterspell (Set Specific)
    counter = UserTrackedCards(card_name="Counterspell", amount=1)
    counter.specifications.append(CardSpecification(set_code="ICE"))

    user.cards.extend([sol, bolt, counter])
    db_session.commit()

    return user


@pytest.fixture
def multiple_users_with_cards(db_session, user_factory, seeded_catalog):
    """
    Seeds multiple users tracking overlapping sets of cards.
    - user1: Sol Ring, Brainstorm
    - user2: Sol Ring, Lurrus of the Dream-Den
    """
    # Create users
    user1 = user_factory(username="user1", password="password")
    user2 = user_factory(username="user2", password="password")

    # Ensure extra cards exist
    # seeded_catalog provides Sol Ring and Brainstorm
    lurrus = Card(name="Lurrus of the Dream-Den")
    lotus = Card(name="Black Lotus")
    db_session.add_all([lurrus, lotus])
    db_session.commit()

    # Retrieve cards
    sol_ring = db_session.query(Card).filter_by(name="Sol Ring").one()
    brainstorm = db_session.query(Card).filter_by(name="Brainstorm").one()

    # Create tracking entries
    # user1 tracks Sol Ring and Brainstorm
    db_session.add(UserTrackedCards(user=user1, card=sol_ring, amount=1))
    db_session.add(UserTrackedCards(user=user1, card=brainstorm, amount=4))

    # user2 tracks Sol Ring and Lurrus
    db_session.add(UserTrackedCards(user=user2, card=sol_ring, amount=2))
    db_session.add(UserTrackedCards(user=user2, card=lurrus, amount=1))

    db_session.commit()

    return [user1, user2]
