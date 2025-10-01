"""
A command-line utility to manually enqueue an RQ task for immediate execution.

This script is intended to be run from within a running backend container
using `docker exec`.

Usage:
    python utilities/trigger_task.py tasks.catalog_tasks.update_full_catalog
"""
import sys
import os

try:
    # Add the application root directory (/app) to the Python path.
    # This ensures that top-level packages like 'managers' and 'utility' can be found.
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

    # Import all task modules to ensure they are registered with the task manager.
    import tasks.card_availability_tasks
    import tasks.catalog_tasks

    from managers.task_manager import queue_task
    from utility import logger
except ImportError as e:
    print(f"❌ Error: Could not import application modules. Details: {e}")
    sys.exit(1) 

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python trigger_task.py <full.path.to.task_function>")
        sys.exit(1)

    task_function_path = sys.argv[1]

    logger.info(f"🚀 Manually enqueuing task: {task_function_path}")
    job = queue_task(task_function_path)
    if job:
        logger.info(f"✅ Task enqueued successfully! Job ID: {job.id}")
    else:
        logger.error("❌ Failed to enqueue task.")
