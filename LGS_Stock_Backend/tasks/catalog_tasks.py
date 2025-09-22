from externals import fetch_scryfall_card_names, fetch_all_sets
from data import database
from utility import logger

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
        set_data_to_add = [
            {
                "code": s.get("code"),
                "name": s.get("name"),
                "release_date": s.get("released_at"),
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
