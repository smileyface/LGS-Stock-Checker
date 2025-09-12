from typing import Any, Dict, List

from utility import logger


def filter_listings(
    card_name: str,
    listings: List[Dict[str, Any]],
    specifications: List[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Filters a list of scraped card listings based on a card name and a list of specific criteria.

    Args:
        card_name: The name of the card to filter for (case-insensitive).
        listings: A list of listing dictionaries scraped from a store.
        specifications: An optional list of dictionaries with filter criteria like
                        'set_code', 'collector_number', and 'finish'. A listing
                        will be included if it matches the card name and *any* of
                        the provided specifications. If no specifications are given,
                        only name is matched.

    Returns:
        A new list containing only the listings that match the criteria.
    """
    filtered_listings = []
    for listing in listings:
        # Basic requirement: card name must match (case-insensitive).
        if card_name.lower() != listing.get("name", "").lower():
            continue

        # If no specifications are provided, a name match is sufficient.
        if not specifications:
            filtered_listings.append(listing)
            continue

        # If specifications are provided, check if the listing matches ANY of them.
        for spec in specifications:
            filter_set_code = spec.get("set_code")
            filter_collector_id = spec.get("collector_number")
            filter_finish = spec.get("finish")

            # Assume it matches until a condition fails for this specific spec.
            set_match = not filter_set_code or filter_set_code.upper() == listing.get("set", "").upper()
            collector_match = not filter_collector_id or str(filter_collector_id) == str(listing.get("collector_number"))
            finish_match = not filter_finish or filter_finish.lower() == "any" or filter_finish.lower() == listing.get("finish", "").lower()

            if set_match and collector_match and finish_match:
                filtered_listings.append(listing)
                # This listing matched one spec, so we add it and move to the next listing.
                break

    logger.debug(f"Filtered {len(listings)} raw listings for '{card_name}' down to {len(filtered_listings)} matching listings.")
    return filtered_listings