import time
from redis import Redis
from rq_scheduler import Scheduler
from datetime import timedelta

from .catalog_tasks import update_card_catalog, update_set_catalog
from .card_availability_tasks import update_wanted_cards_availability
from utility import logger

# --- Configuration ---
REDIS_HOST = "redis"
REDIS_PORT = 6379
# Run the catalog update once every 24 hours
CATALOG_UPDATE_INTERVAL_HOURS = 24
CATALOG_TASK_ID = "scheduled_catalog_update"
SET_CATALOG_TASK_ID = "scheduled_set_catalog_update"

# Run the availability check every 15 minutes
AVAILABILITY_UPDATE_INTERVAL_MINUTES = 15
AVAILABILITY_TASK_ID = "scheduled_availability_update"


def schedule_tasks():
    """
    Connects to rq-scheduler and schedules all recurring tasks for the application.
    This function is designed to be idempotent; it won't create duplicate scheduled jobs.
    """
    logger.info("🚀 Setting up scheduled tasks...")
    try:
        redis_conn = Redis(host=REDIS_HOST, port=REDIS_PORT)
        scheduler = Scheduler(connection=redis_conn)

        # --- Schedule Card Catalog Update ---
        # Check if the job is already scheduled to avoid duplicates on restart
        if CATALOG_TASK_ID not in scheduler:
            logger.info(f"🗓️ Scheduling task '{CATALOG_TASK_ID}' to run every {CATALOG_UPDATE_INTERVAL_HOURS} hours.")
            scheduler.schedule(
                scheduled_time=time.time(),
                func=update_card_catalog,
                interval=timedelta(hours=CATALOG_UPDATE_INTERVAL_HOURS).total_seconds(),
                job_id=CATALOG_TASK_ID,
                description="Periodically updates the card catalog from Scryfall."
            )

        # --- Schedule Set Catalog Update ---
        if SET_CATALOG_TASK_ID not in scheduler:
            logger.info(f"🗓️ Scheduling task '{SET_CATALOG_TASK_ID}' to run every {CATALOG_UPDATE_INTERVAL_HOURS} hours.")
            scheduler.schedule(
                scheduled_time=time.time(),
                func=update_set_catalog,
                interval=timedelta(hours=CATALOG_UPDATE_INTERVAL_HOURS).total_seconds(),
                job_id=SET_CATALOG_TASK_ID,
                description="Periodically updates the set catalog from Scryfall."
            )

        # --- Schedule Availability Check ---
        if AVAILABILITY_TASK_ID not in scheduler:
            logger.info(f"🗓️ Scheduling task '{AVAILABILITY_TASK_ID}' to run every {AVAILABILITY_UPDATE_INTERVAL_MINUTES} minutes.")
            scheduler.schedule(
                scheduled_time=time.time(),
                func=update_wanted_cards_availability, # Call with no arguments for a system-wide update
                interval=timedelta(minutes=AVAILABILITY_UPDATE_INTERVAL_MINUTES).total_seconds(),
                job_id=AVAILABILITY_TASK_ID,
                description="Periodically checks for card availability for all users."
            )
    except Exception as e:
        logger.error(f"❌ Failed to schedule tasks: {e}")
