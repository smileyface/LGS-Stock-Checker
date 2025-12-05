from externals import (
    fetch_scryfall_card_names,
    fetch_all_sets,
    fetch_all_card_data,
)
from managers import task_manager
from managers import redis_manager
from utility import logger
from datetime import datetime
import time


# --- Constants ---
CHUNK_SIZE = 20000


# --- Tasks ---
@task_manager.task()
def update_card_catalog():
    """
    Task to fetch all card names from Scryfall and update the
    local database catalog. This is intended to be run as a background job.
    """
    logger.info("🚀 Starting background task: update_card_catalog")

    card_names = fetch_scryfall_card_names()

    if card_names:
        logger.info(
            f"🗂️ Fetched {len(card_names)} card names from source. "
            f"Updating database catalog..."
        )
        redis_manager.publish_pubsub("catalog_card_names_result",
                                     {"names": card_names})

    logger.info("🏁 Finished background task: update_card_catalog")


@task_manager.task()
def update_set_catalog():
    """
    Task to fetch all set data from Scryfall and update the local database
    catalog. This is intended to be run as a background job.
    """
    logger.info("🚀 Starting background task: update_set_catalog")

    raw_set_data = fetch_all_sets()

    if raw_set_data:
        # Transform the data to match the database schema
        # ('released_at' -> 'release_date')
        # and convert date strings to Python date objects for
        # SQLite compatibility.
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
            if s.get("code")
            and s.get("name")  # Ensure essential fields are present
        ]
        logger.info(
            f"🗂️ Fetched and processed {len(set_data_to_add)} sets from "
            f"source. Updating database catalog..."
        )
        redis_manager.publish_pubsub("catalog_set_data_result",
                                     {"sets": set_data_to_add})

        logger.info("✅ Successfully updated set catalog in the database.")
    else:
        logger.warning(
            "⚠️ Could not fetch set data from source. Catalog update skipped."
        )

    logger.info("🏁 Finished background task: update_set_catalog")


@task_manager.task()
def update_full_catalog():
    """
    Task to fetch all card printings from Scryfall and populate the
    finishes, card_printings, and their association tables.
    """
    # --- Enforce Dependency ---
    # Ensure the main card catalog is populated before processing printings.
    logger.info(
        "Ensuring main card catalog is up-to-date before "
        "processing printings..."
    )
    update_set_catalog()
    update_card_catalog()
    logger.info("🚀 Starting background task: update_full_catalog")
    start_time = time.monotonic()

    total_cards_processed = 0
    try:
        card_data_stream = fetch_all_card_data()
        if not card_data_stream:
            logger.warning(
                "Card data stream is empty. Aborting catalog update."
            )
            return

        # Process the stream in chunks to keep memory usage low.
        all_finishes_found = set()
        printings_chunk = []

        logger.info(f"Processing card data stream in chunks of "
                    f"{CHUNK_SIZE}...")
        chunk_start_time = time.monotonic()
        for i, card in enumerate(card_data_stream, 1):
            total_cards_processed = i
            # 1. Extract unique finishes
            for finish in card.get("finishes", []):
                all_finishes_found.add(finish)

            # 2. Extract printings
            if (
                card.get("name")
                and card.get("set")
                and card.get("collector_number")
                and card.get("finishes")
            ):
                printings_chunk.append(
                    {
                        "card_name": card["name"],
                        "set_code": card["set"],
                        "collector_number": card["collector_number"],
                        "finishes": card["finishes"],
                    }
                )

            # When a chunk is full, process it.
            if i % CHUNK_SIZE == 0:
                chunk_duration = time.monotonic() - chunk_start_time
                logger.info(f"Publishing chunk of {len(printings_chunk)}\
                             printings... (took {chunk_duration:.2f}s)")
                redis_manager.publish_pubsub("catalog_printings_chunk_result",
                                             {"printings": printings_chunk})
                printings_chunk = []
                chunk_start_time = time.monotonic()

        # Process any remaining items in the last partial chunk
        if printings_chunk:
            logger.info("Processing final chunk...")
            redis_manager.publish_pubsub("catalog_printings_chunk_result",
                                         {"printings": printings_chunk})

        # Add all unique finishes found across all chunks at the end
        if all_finishes_found:
            logger.info(
                f"Found {len(all_finishes_found)} unique finishes. "
                f"Updating database."
            )
            redis_manager.publish_pubsub("catalog_finishes_chunk_result",
                                         {"finishes": list(all_finishes_found)
                                          })

    except Exception as e:
        logger.error(
            f"An error occurred during update_full_catalog: {e}", exc_info=True
        )
    finally:
        total_duration = time.monotonic() - start_time
        logger.info(
            f"🏁 Finished background task: update_full_catalog. "
            f"Processed {total_cards_processed} cards in "
            f"{total_duration:.2f} seconds."
        )
