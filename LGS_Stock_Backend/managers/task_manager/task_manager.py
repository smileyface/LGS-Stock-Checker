from managers.redis_manager import scheduler, queue
from . import task_definitions
from utility import logger

# --- Task Registry ---
# This dictionary will be populated by task modules at application startup.
# This avoids circular imports by allowing tasks to register themselves.
TASK_REGISTRY = {}

def task(task_id: str = None):
    """
    A decorator that registers a function as a background task with both RQ and our internal task manager.
    This replaces the need for separate `register_task` calls.

    Usage:
        @task_manager.task
        def my_task_function(arg1, arg2):
            # ...

    Args:
        task_id (str, optional): The ID to register the task with. If None, the function's name is used.
    """
    def decorator(func):
        # Use the provided task_id or default to the function's name
        _task_id = task_id or func.__name__
        # 1. Register with our internal registry for queuing by ID
        register_task(_task_id, func)
        # 2. Decorate with RQ's task decorator so workers can execute it
        return queue.task(func)
    return decorator

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
 
