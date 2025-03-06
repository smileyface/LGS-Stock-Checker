import json
import os
from datetime import datetime, timedelta

import redis
from rq import Queue
from rq_scheduler import Scheduler
from utility.logger import logger

# Detect if running inside Docker or on Windows
if os.getenv("RUNNING_IN_DOCKER"):
    REDIS_HOST = "redis"  # Use "redis" inside Docker
else:
    REDIS_HOST = "localhost"  # Use "localhost" on Windows
REDIS_PORT = 6379
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}"

redis_conn = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
queue = Queue(connection=redis_conn)
scheduler = Scheduler(queue=queue, connection=redis_conn)
functions = {}  # Registry for callable functions


def register_function(self, name, func):
    """Allows modules to register functions for Redis tasks."""
    self.functions[name] = func
    logger.info(f"🔗 Registered Redis function: {name}")


def queue_task(self, func_name, *args, **kwargs):
    """Queues a task by registered function name."""
    if func_name in self.functions:
        self.queue.enqueue(self.functions[func_name], *args, **kwargs)
        logger.info(f"📌 Queued task: {func_name}")
    else:
        logger.error(f"❌ Attempted to queue unknown task: {func_name}")


def schedule_task(self, func, interval_hours, *args, **kwargs):
    """Schedules a recurring task."""
    job_id = f"scheduled_{func.__name__}"  # Use function name dynamically

    logger.debug(f"📌 Count of jobs already in the queue: {self.scheduler.count()}")

    self.scheduler.count()
    existing_jobs = list(self.scheduler.get_jobs())  # Convert generator to list

    existing_job = next((job for job in existing_jobs if job.id == job_id), None)

    if existing_job:
        self.scheduler.cancel(existing_job)
        logger.info(f"🔄 Rescheduling {func.__name__} every {interval_hours} hours.")

    scheduled_time = datetime.utcnow() + timedelta(hours=interval_hours)

    self.scheduler.schedule(
        scheduled_time=scheduled_time,
        func=func,
        args=args,
        kwargs=kwargs,
        interval=interval_hours * 3600,
        repeat=None
    )

    logger.info(f"✅ Scheduled {func.__name__} every {interval_hours} hours.")


