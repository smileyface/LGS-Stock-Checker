from externals import fetch_scryfall_card_names, fetch_all_sets, fetch_all_card_data
from data import database
from managers import task_manager
from utility import logger
from datetime import datetime
import time

@task_manager.task()
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


@task_manager.task()
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


@task_manager.task()
def update_full_catalog():
    """
    Task to fetch all card printings from Scryfall and populate the
    finishes, card_printings, and their association tables.
    """
    logger.info("🚀 Starting background task: update_full_catalog")
    start_time = time.monotonic()

    try:
        card_data_stream = fetch_all_card_data()
        if not card_data_stream:
            logger.warning("Card data stream is empty. Aborting catalog update.")
            return

        # Process the stream in chunks to keep memory usage low.
        chunk_size = 20000
        all_finishes = set()
        printings_chunk = []
        associations_chunk_temp = []
        total_cards_processed = 0

        logger.info(f"Processing card data stream in chunks of {chunk_size}...")
        chunk_start_time = time.monotonic()
        for i, card in enumerate(card_data_stream, 1):
            total_cards_processed = i
            # 1. Extract unique finishes
            for finish in card.get("finishes", []):
                all_finishes.add(finish)

            # 2. Extract printings
            if card.get("name") and card.get("set") and card.get("collector_number"):
                printings_chunk.append({
                    "card_name": card["name"],
                    "set_code": card["set"],
                    "collector_number": card["collector_number"],
                })
                associations_chunk_temp.append(card)

            # When a chunk is full, process it.
            if i % chunk_size == 0:
                chunk_duration = time.monotonic() - chunk_start_time
                logger.info(f"Processing chunk up to card {i}... (took {chunk_duration:.2f}s)")
                _process_catalog_chunk(printings_chunk, associations_chunk_temp)
                # Clear chunks for the next iteration
                printings_chunk = []
                associations_chunk_temp = []
                chunk_start_time = time.monotonic() # Reset timer for next chunk

        # Process any remaining items in the last partial chunk
        if printings_chunk:
            logger.info("Processing final chunk...")
            _process_catalog_chunk(printings_chunk, associations_chunk_temp)

        # Add all unique finishes found across all chunks at the end
        if all_finishes:
            logger.info(f"Found {len(all_finishes)} unique finishes. Updating database...")
            database.bulk_add_finishes(list(all_finishes))

    except Exception as e:
        logger.error(f"An error occurred during update_full_catalog: {e}", exc_info=True)
    finally:
        total_duration = time.monotonic() - start_time
        logger.info(f"🏁 Finished background task: update_full_catalog. Processed {total_cards_processed} cards in {total_duration:.2f} seconds.")


def _process_catalog_chunk(printings_to_add, associations_to_add_temp):
    """Helper function to process one chunk of card data."""
    if not printings_to_add:
        return

    logger.info(f"Adding {len(printings_to_add)} printings to database...")
    database.bulk_add_card_printings(printings_to_add)

    # Get maps of all printings and finishes to resolve IDs
    printings_map = database.get_all_printings_map()
    finishes_map = database.get_all_finishes_map()

    associations_to_add = []
    for card in associations_to_add_temp:
        printing_key = (card.get("name"), card.get("set"), card.get("collector_number"))
        printing_id = printings_map.get(printing_key)

        if printing_id:
            for finish_name in card.get("finishes", []):
                finish_id = finishes_map.get(finish_name)
                if finish_id:
                    associations_to_add.append({"printing_id": printing_id, "finish_id": finish_id})

    if associations_to_add:
        logger.info(f"Adding {len(associations_to_add)} printing-finish associations...")
        database.bulk_add_printing_finish_associations(associations_to_add)
