import pytest
from data.database.models.orm_models import Card, Set, Finish, CardPrinting
from data.database.repositories.card_repository import get_printings_for_card


@pytest.fixture
def seeded_printings(db_session):
    """Fixture to create a card with multiple printings and finishes."""
    # Seed lookup tables
    db_session.add_all([
        Card(name="Sol Ring"),
        Set(code="C21", name="Commander 2021"),
        Set(code="LTC", name="The Lord of the Rings: Tales of Middle-earth Commander"),
        Finish(name="nonfoil"),
        Finish(name="foil"),
        Finish(name="etched")
    ])
    db_session.commit()

    # Create printings
    printing1 = CardPrinting(card_name="Sol Ring", set_code="C21", collector_number="125")
    printing2 = CardPrinting(card_name="Sol Ring", set_code="LTC", collector_number="3")
    db_session.add_all([printing1, printing2])
    db_session.commit()

    # Associate finishes
    # The query orders by name, so the result order is 'etched', 'foil', 'nonfoil'.
    # We must unpack into variables that match this order.
    etched, foil, nonfoil = db_session.query(Finish).order_by(Finish.name).all()

    printing1.available_finishes.extend([nonfoil, foil])
    printing2.available_finishes.extend([nonfoil, etched])
    db_session.commit()


def test_get_printings_for_card(seeded_printings):
    """
    Tests that get_printings_for_card correctly retrieves all printings
    and their associated finishes for a given card.
    """
    printings = get_printings_for_card("Sol Ring")

    assert len(printings) == 2

    # Check C21 printing
    assert printings[0]["set_code"] == "C21"
    assert printings[0]["collector_number"] == "125"
    assert sorted(printings[0]["finishes"]) == ["foil", "nonfoil"]

    # Check LTC printing
    assert printings[1]["set_code"] == "LTC"
    assert printings[1]["collector_number"] == "3"
    assert sorted(printings[1]["finishes"]) == ["etched", "nonfoil"]

    # Check for a card with no printings
    assert get_printings_for_card("Black Lotus") == []
