import time
from datetime import timedelta

from .catalog_tasks import update_card_catalog, update_set_catalog, update_full_catalog
from .card_availability_tasks import update_wanted_cards_availability
from managers.redis_manager import scheduler
from managers.task_manager import task_definitions
from utility import logger

# --- Configuration ---
# Run the catalog update once every 24 hours
CATALOG_UPDATE_INTERVAL_HOURS = 24

# Run the availability check every 15 minutes
AVAILABILITY_UPDATE_INTERVAL_MINUTES = 15


def schedule_tasks():
    """
    Connects to rq-scheduler and schedules all recurring tasks for the application.
    This function is designed to be idempotent; it won't create duplicate scheduled jobs.
    """
    logger.info("🚀 Setting up scheduled tasks...")
    try:
        # --- Schedule Card Catalog Update ---
        # Check if the job is already scheduled to avoid duplicates on restart
        if task_definitions.CATALOG_TASK_ID not in scheduler:
            logger.info(f"🗓️ Scheduling task '{task_definitions.CATALOG_TASK_ID}' to run every {CATALOG_UPDATE_INTERVAL_HOURS} hours.")
            scheduler.schedule(
                scheduled_time=time.time(),
                func=update_card_catalog,
                interval=timedelta(hours=CATALOG_UPDATE_INTERVAL_HOURS).total_seconds(),
                job_id=task_definitions.CATALOG_TASK_ID,
                description="Periodically updates the card catalog from Scryfall."
            )

        # --- Schedule Set Catalog Update ---
        if task_definitions.SET_CATALOG_TASK_ID not in scheduler:
            logger.info(f"🗓️ Scheduling task '{task_definitions.SET_CATALOG_TASK_ID}' to run every {CATALOG_UPDATE_INTERVAL_HOURS} hours.")
            scheduler.schedule(
                scheduled_time=time.time(),
                func=update_set_catalog,
                interval=timedelta(hours=CATALOG_UPDATE_INTERVAL_HOURS).total_seconds(),
                job_id=task_definitions.SET_CATALOG_TASK_ID,
                description="Periodically updates the set catalog from Scryfall."
            )

        # --- Schedule Full Catalog Update ---
        # This is a more comprehensive update that includes printings and finishes.
        if task_definitions.FULL_CATALOG_TASK_ID not in scheduler:
            logger.info(f"🗓️ Scheduling task '{task_definitions.FULL_CATALOG_TASK_ID}' to run every {CATALOG_UPDATE_INTERVAL_HOURS} hours.")
            scheduler.schedule(
                scheduled_time=time.time(),
                func=update_full_catalog,
                interval=timedelta(hours=CATALOG_UPDATE_INTERVAL_HOURS).total_seconds(),
                job_id=task_definitions.FULL_CATALOG_TASK_ID,
                description="Periodically updates the full card, set, printing, and finish catalog from Scryfall."
            )

        # --- Schedule Availability Check ---
        if task_definitions.AVAILABILITY_TASK_ID not in scheduler:
            logger.info(f"🗓️ Scheduling task '{task_definitions.AVAILABILITY_TASK_ID}' to run every {AVAILABILITY_UPDATE_INTERVAL_MINUTES} minutes.")
            scheduler.schedule(
                scheduled_time=time.time(),
                func=update_wanted_cards_availability, # Call with no arguments for a system-wide update
                interval=timedelta(minutes=AVAILABILITY_UPDATE_INTERVAL_MINUTES).total_seconds(),
                job_id=task_definitions.AVAILABILITY_TASK_ID,
                description="Periodically checks for card availability for all users."
            )
    except Exception as e:
        logger.error(f"❌ Failed to schedule tasks: {e}")
