from managers.redis_manager import scheduler, queue
from . import task_definitions
from utility import logger

# --- Task Registry ---
# This dictionary will be populated by task modules at application startup.
# This avoids circular imports by allowing tasks to register themselves.
TASK_REGISTRY = {}

def register_task(task_id: str, func: callable):
    """Allows task modules to register their functions with the task manager."""
    if task_id in TASK_REGISTRY:
        logger.warning(f"⚠️ Task ID '{task_id}' is being re-registered. This may be unintentional.")
    TASK_REGISTRY[task_id] = func
    logger.debug(f"✅ Registered task '{task_id}' to function '{func.__name__}'.")

def queue_task(task_id: str, *args, **kwargs):
    """
    Queues a task by its ID to be executed by an RQ worker.

    Args:
        task_id (str): The ID of the task to execute, as defined in the TASK_REGISTRY.
        *args: Positional arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.
    """
    func = TASK_REGISTRY.get(task_id)
    if not func:
        logger.error(f"❌ Attempted to queue unknown task with ID: '{task_id}'")
        return

    try:
        queue.enqueue(func, *args, **kwargs)
        # Use func.__name__ to get the name of the function for logging.
        logger.info(f"📌 Queued task '{task_id}' ({func.__name__})")
    except Exception as e:
        logger.error(f"❌ Failed to queue task '{task_id}': {e}")


def trigger_scheduled_task(task_id: str):
    """
    Manually triggers a specific scheduled task to run immediately.
    This is useful for testing or for administrative overrides.

    Args:
        task_id (str): The unique ID of the scheduled job to trigger.
    """
    logger.info(f"⚡ Attempting to trigger scheduled task: {task_id}")
    try:
        job = scheduler.fetch_job(task_id)
        if job:
            # Enqueue the job immediately for a worker to pick up.
            scheduler.enqueue_job(job)
            logger.info(f"✅ Successfully triggered scheduled task: {task_id}")
        else:
            logger.warning(f"⚠️ Scheduled task '{task_id}' not found. Cannot trigger.")
    except Exception as e:
        logger.error(f"❌ Failed to trigger scheduled task '{task_id}': {e}")
 
