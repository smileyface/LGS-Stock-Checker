from externals import fetch_scryfall_card_names, fetch_all_sets, fetch_all_card_data
from data import database
from utility import logger
from datetime import datetime

def update_card_catalog():

    """
    Task to fetch all card names from Scryfall and update the local database catalog.
    This is intended to be run as a background job.
    """
    logger.info("🚀 Starting background task: update_card_catalog")

    card_names = fetch_scryfall_card_names()

    if card_names:
        logger.info(f"🗂️ Fetched {len(card_names)} card names from source. Updating database catalog...")
        database.add_card_names_to_catalog(card_names)
        logger.info("✅ Successfully updated card catalog in the database.")
    else:
        logger.warning("⚠️ Could not fetch card names from source. Catalog update skipped.")

    logger.info("🏁 Finished background task: update_card_catalog")


def update_set_catalog():
    """
    Task to fetch all set data from Scryfall and update the local database catalog.
    This is intended to be run as a background job.
    """
    logger.info("🚀 Starting background task: update_set_catalog")

    raw_set_data = fetch_all_sets()

    if raw_set_data:
        # Transform the data to match the database schema ('released_at' -> 'release_date')
        # and convert date strings to Python date objects for SQLite compatibility.
        set_data_to_add = [
            {
                "code": s.get("code"),
                "name": s.get("name"),
                "release_date": (
                    datetime.strptime(s.get("released_at"), "%Y-%m-%d").date()
                    if s.get("released_at")
                    else None
                ),
            }
            for s in raw_set_data
            if s.get("code") and s.get("name") # Ensure essential fields are present
        ]
        logger.info(f"🗂️ Fetched and processed {len(set_data_to_add)} sets from source. Updating database catalog...")
        database.add_set_data_to_catalog(set_data_to_add)
        logger.info("✅ Successfully updated set catalog in the database.")
    else:
        logger.warning("⚠️ Could not fetch set data from source. Catalog update skipped.")

    logger.info("🏁 Finished background task: update_set_catalog")


def update_full_catalog():
    """
    Task to fetch all card printings from Scryfall and populate the
    finishes, card_printings, and their association tables.
    """
    logger.info("🚀 Starting background task: update_full_catalog")

    all_card_data = fetch_all_card_data()
    if not all_card_data:
        logger.warning("⚠️ Could not fetch full card data from source. Catalog update skipped.")
        return

    # 1. Extract and add all unique finishes
    all_finishes = set(finish for card in all_card_data for finish in card.get("finishes", []))

    if all_finishes:
        logger.info(f"Found {len(all_finishes)} unique finishes. Updating database...")
        database.bulk_add_finishes(list(all_finishes))

    # 2. Extract and add all unique card printings
    printings_to_add = [
        {
            "card_name": card["name"],
            "set_code": card["set"],
            "collector_number": card["collector_number"],
        }
        for card in all_card_data
        if card.get("name") and card.get("set") and card.get("collector_number")
    ]

    if printings_to_add:
        logger.info(f"Found {len(printings_to_add)} unique printings. Updating database...")
        database.bulk_add_card_printings(printings_to_add)

    # 3. Create associations between printings and finishes
    logger.info("Building printing-to-finish associations...")
    printings_map = database.get_all_printings_map()
    finishes_map = database.get_all_finishes_map()

    associations_to_add = []
    for card in all_card_data:
        printing_key = (card.get("name"), card.get("set"), card.get("collector_number"))
        printing_id = printings_map.get(printing_key)

        if printing_id:
            for finish_name in card.get("finishes", []):
                finish_id = finishes_map.get(finish_name)
                if finish_id:
                    associations_to_add.append({"printing_id": printing_id, "finish_id": finish_id})

    if associations_to_add:
        logger.info(f"Found {len(associations_to_add)} printing-finish associations. Updating database...")
        database.bulk_add_printing_finish_associations(associations_to_add)

    logger.info("🏁 Finished background task: update_full_catalog")
