from typing import Any, Dict, List

from utility.logger import logger


def filter_listings(
    card_name: str,
    listings: List[Dict[str, Any]],
    specifications: Dict[str, Any] = None,
) -> List[Dict[str, Any]]:
    """
    Filters a list of scraped card listings based on a card name and specific criteria.

    Args:
        card_name: The name of the card to filter for (case-insensitive).
        listings: A list of listing dictionaries scraped from a store.
        specifications: An optional dictionary with filter criteria like
                        'set_code', 'collector_number', and 'finish'.

    Returns:
        A new list containing only the listings that match the criteria.
    """
    if specifications is None:
        specifications = {}

    filter_set_code = specifications.get("set_code")
    filter_collector_id = specifications.get("collector_number")
    filter_finish = specifications.get("finish")

    filtered_listings = []
    for listing in listings:
        if card_name.lower() != listing.get("name", "").lower():
            continue
        if filter_set_code and filter_set_code.upper() != listing.get("set", "").upper():
            continue
        if filter_collector_id and filter_collector_id != listing.get("collector_number"):
            continue
        if filter_finish and filter_finish.lower() != "any" and filter_finish.lower() != listing.get("finish", "").lower():
            continue
        filtered_listings.append(listing)

    logger.debug(f"Filtered {len(listings)} listings for '{card_name}' down to {len(filtered_listings)}")
    return filtered_listings