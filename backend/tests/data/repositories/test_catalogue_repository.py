from data.database.repositories.catalogue_repository import get_printings_for_card


def test_get_printings_for_card(seeded_printings):
    """
    Tests that get_printings_for_card correctly retrieves all printings
    and their associated finishes for a given card.
    """
    printings = get_printings_for_card("Sol Ring")

    assert len(printings) == 3

    # The query orders by set_code, so we assert in that order: C21, LTC, ONE
    # Check C21 printing (index 0)
    assert printings[0]["set_code"] == "C21"
    assert printings[0]["collector_number"] == "125"
    assert sorted(printings[0]["finishes"]) == ["foil", "non-foil"]

    # Check LTC printing (index 1)
    assert printings[1]["set_code"] == "LTC"
    assert printings[1]["collector_number"] == "3"
    assert sorted(printings[1]["finishes"]) == ["etched", "non-foil"]

    # Check ONE printing (index 2)
    assert printings[2]["set_code"] == "ONE"
    assert printings[2]["collector_number"] == "254"
    assert sorted(printings[2]["finishes"]) == ["foil", "non-foil"]

    # Check for a card with no printings
    assert get_printings_for_card("Black Lotus") == []
