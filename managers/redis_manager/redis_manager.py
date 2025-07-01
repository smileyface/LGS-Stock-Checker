import os
from datetime import datetime, timedelta

import redis
from rq import Queue
from rq_scheduler import Scheduler

from utility.logger import logger

# Use an environment variable for the job queue's Redis URL.
# This is more flexible than detecting the OS.
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# The job queue manager connects to Redis for its specific purpose.
redis_job_conn = redis.from_url(REDIS_URL) # RQ expects bytes, so no decode_responses
queue = Queue(connection=redis_job_conn)
scheduler = Scheduler(queue=queue, connection=redis_job_conn)
functions = {}  # Registry for callable functions


def register_function(name: str, func: callable):
    """Allows modules to register functions for Redis tasks."""
    functions[name] = func
    logger.info(f"🔗 Registered Redis function: {name}")


def queue_task(func_name: str, *args, **kwargs):
    """Queues a task by registered function name."""
    if func_name in functions:
        queue.enqueue(functions[func_name], *args, **kwargs)
        logger.info(f"📌 Queued task: {func_name}")
    else:
        logger.error(f"❌ Attempted to queue unknown task: {func_name}")


def schedule_task(func: callable, interval_hours: int, *args, **kwargs):
    """Schedules a recurring task."""
    job_id = f"scheduled_{func.__name__}"  # Use function name dynamically
    logger.debug(f"📌 Count of jobs already in the queue: {scheduler.count()}")
    # Check if a job with the same ID already exists and cancel it to reschedule.
    if job_id in scheduler:
        scheduler.cancel(job_id)
        logger.info(f"🔄 Rescheduling {func.__name__} every {interval_hours} hours.")

    scheduled_time = datetime.utcnow() + timedelta(hours=interval_hours)

    scheduler.schedule(
        scheduled_time=scheduled_time,
        func=func,
        args=args,
        kwargs=kwargs,
        interval=interval_hours * 3600,
        repeat=None
    )

    logger.info(f"✅ Scheduled {func.__name__} every {interval_hours} hours.")
