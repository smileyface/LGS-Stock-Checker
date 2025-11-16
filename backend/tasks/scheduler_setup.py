from typing import Callable
from datetime import timedelta, datetime

from managers import redis_manager
from managers import task_manager
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
    if task_id not in redis_manager.scheduler:
        logger.info(
            f"🗓️ Scheduling task '{task_id}' to run every "
            f"{interval_seconds / 60:.0f} minutes."
        )
        redis_manager.scheduler.schedule(
            scheduled_time=initial_run_time,
            func=func,
            interval=interval_seconds,
            id=task_id,
            description=description,
        )


def schedule_recurring_tasks():
    """
    Connects to rq-scheduler and schedules all
    recurring tasks for the application.
    This function is designed to be idempotent; it
    won't create duplicate scheduled jobs.
    """
    logger.info("🚀 Setting up scheduled tasks...")
    try:
        initial_run_time = datetime.now()
        catalog_interval = timedelta(
            hours=CATALOG_UPDATE_INTERVAL_HOURS
        ).total_seconds()
        availability_interval = timedelta(
            minutes=AVAILABILITY_UPDATE_INTERVAL_MINUTES
        ).total_seconds()

        # --- Schedule the Main Catalog Update Task ---
        # This single task will handle its own dependencies
        # (cards, sets) internally.
        # We pass the function's import path as a string, which is
        # the correct way for RQ.
        _schedule_if_not_exists(
            task_id=task_manager.task_definitions.FULL_CATALOG_TASK_ID,
            func="tasks.catalog_tasks.update_full_catalog",
            interval_seconds=catalog_interval,
            description="Periodically updates the full card, set, printing, "
                        "and finish catalog from Scryfall.",
            initial_run_time=initial_run_time,
        )
        logger.info("✅ Successfully scheduled the main catalog update task.")

        # --- Schedule Availability Check ---
        _schedule_if_not_exists(
            task_id=task_manager.task_definitions.AVAILABILITY_TASK_ID,
            func="tasks.card_availability_tasks."
            "update_all_tracked_cards_availability",
            interval_seconds=availability_interval,
            description="Periodically checks for card availability "
                        "for all users.",
            initial_run_time=initial_run_time,
        )
        logger.info("✅ Successfully scheduled the availability check task.")
    except Exception as e:
        logger.error(f"❌ Failed to schedule tasks: {e}")
    logger.info("🏁 Finished setting up scheduled tasks.")
