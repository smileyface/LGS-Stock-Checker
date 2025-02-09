import os

import redis
from rq import Queue
from rq_scheduler import Scheduler
from datetime import timedelta
from utility.logger import logger

# Detect if running inside Docker or on Windows
if os.getenv("RUNNING_IN_DOCKER"):
    REDIS_HOST = "redis"  # Use "redis" inside Docker
else:
    REDIS_HOST = "localhost"  # Use "localhost" on Windows
REDIS_PORT = 6379
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}"

class RedisManager:
    """Handles Redis connections, queues, and scheduled tasks."""
    def __init__(self):
        self.redis_conn = redis.Redis()
        self.queue = Queue(connection=self.redis_conn)
        self.scheduler = Scheduler(queue=self.queue, connection=self.redis_conn)
        self.functions = {}  # Registry for callable functions

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

    def schedule_task(self, func_name, interval_hours, *args, **kwargs):
        """Schedules a recurring task."""
        job_id = f"scheduled_{func_name}"
        existing_jobs = self.scheduler.get_jobs()
        existing_job = next((job for job in existing_jobs if job.id == job_id), None)

        if existing_job:
            self.scheduler.cancel(existing_job)
            logger.info(f"🔄 Rescheduling {func_name} every {interval_hours} hours.")

        self.scheduler.schedule(
            scheduled_time=timedelta(hours=interval_hours),
            func=self.functions[func_name],
            args=args,
            kwargs=kwargs,
            interval=interval_hours * 3600,
            repeat=None,
            id=job_id
        )

        logger.info(f"✅ Scheduled {func_name} every {interval_hours} hours.")

    def store_data(self, key, data):
        """Stores data in Redis."""
        self.redis_conn.set(key, data)
        logger.info(f"💾 Stored data under key: {key}")

    def load_data(self, key):
        """Loads data from Redis."""
        data = self.redis_conn.get(key)
        return data if data else None

# Singleton instance
redis_manager = RedisManager()