from typing import Callable
from datetime import timedelta, datetime

from .catalog_tasks import update_card_catalog, update_set_catalog, update_full_catalog
from .card_availability_tasks import update_all_tracked_cards_availability
from managers.redis_manager import scheduler
from managers.task_manager import task_definitions
from utility import logger

# --- Configuration ---
# Run the catalog update once every 24 hours
CATALOG_UPDATE_INTERVAL_HOURS = 24

# Run the availability check every 15 minutes
AVAILABILITY_UPDATE_INTERVAL_MINUTES = 15


def _schedule_if_not_exists(
    task_id: str,
    func: Callable,
    interval_seconds: float,
    description: str,
    initial_run_time: datetime,
):
    """
    Checks if a task is already scheduled and schedules it if not.

    Args:
        task_id: The unique ID for the task.
        func: The task function to execute.
        interval_seconds: The execution interval in seconds.
        description: A description of the task.
        initial_run_time: The time for the first run.
    """
    if task_id not in scheduler:
        logger.info(f"🗓️ Scheduling task '{task_id}' to run every {interval_seconds / 60:.0f} minutes.")
        scheduler.schedule(
            scheduled_time=initial_run_time,
            func=func,
            interval=interval_seconds,
            id=task_id,
            description=description,
        )


def schedule_tasks():
    """
    Connects to rq-scheduler and schedules all recurring tasks for the application.
    This function is designed to be idempotent; it won't create duplicate scheduled jobs.
    """
    logger.info("🚀 Setting up scheduled tasks...")
    try:
        initial_run_time = datetime.now()
        catalog_interval = timedelta(hours=CATALOG_UPDATE_INTERVAL_HOURS).total_seconds()
        availability_interval = timedelta(minutes=AVAILABILITY_UPDATE_INTERVAL_MINUTES).total_seconds()

        # --- Schedule Catalog Updates ---
        _schedule_if_not_exists(task_definitions.CATALOG_TASK_ID, update_card_catalog, catalog_interval, "Periodically updates the card catalog from Scryfall.", initial_run_time)
        _schedule_if_not_exists(task_definitions.SET_CATALOG_TASK_ID, update_set_catalog, catalog_interval, "Periodically updates the set catalog from Scryfall.", initial_run_time)
        _schedule_if_not_exists(task_definitions.FULL_CATALOG_TASK_ID, update_full_catalog, catalog_interval, "Periodically updates the full card, set, printing, and finish catalog from Scryfall.", initial_run_time)

        # --- Schedule Availability Check ---
        _schedule_if_not_exists(
            task_id=task_definitions.AVAILABILITY_TASK_ID,
            func=update_all_tracked_cards_availability,
            interval_seconds=availability_interval,
            description="Periodically checks for card availability for all users.",
            initial_run_time=initial_run_time,
        )
    except Exception as e:
        logger.error(f"❌ Failed to schedule tasks: {e}")
