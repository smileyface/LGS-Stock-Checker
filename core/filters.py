def filter_listings(card_filter, listings):
    """
    Filters listings based on the provided card filter criteria.
    """
    filtered_listings = []

    for listing in listings:
        # Check card name (mandatory)
        if card_filter["card_name"].lower() not in listing["name"].lower():
            continue

        # Check set code (optional)
        if card_filter["set_code"] and card_filter["set_code"] != listing.get("set"):
            continue

        # Check collector ID (optional)
        if card_filter["collector_id"] and card_filter["collector_id"] != listing.get("collector_number"):
            continue

        # Check foil (optional)
        if card_filter["foil"] and listing.get("finish") != "foil":
            continue

        # If all criteria match, add to the filtered list
        filtered_listings.append(listing)

    return filtered_listings