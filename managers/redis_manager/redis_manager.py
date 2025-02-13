import json
import logging
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

class RedisManager:
    """Handles Redis connections, queues, and scheduled tasks."""
    def __init__(self):
        logging.info(f"Connecting to Redis at: " + REDIS_URL)
        self.redis_conn = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
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

    def get_safe_jobs(self, scheduler):
        """Retrieve jobs safely, ensuring no decode errors."""
        try:
            job_ids = scheduler.connection.zrange(scheduler.scheduled_jobs_key, 0, -1)
            logger.debug(f"🔍 Raw job data from Redis -> {job_ids}")

            # Ensure we don't call `.decode()` on a str
            job_ids = [job_id if isinstance(job_id, str) else job_id.decode("utf-8") for job_id in job_ids]

            return set(job_ids)
        except Exception as e:
            logger.error(f"❌ Error calling get_jobs(): {e}")
            return set()


    def schedule_task(self, func_name, interval_hours, *args, **kwargs):
        """Schedules a recurring task while ensuring jobs are properly handled."""

        existing_jobs = self.get_safe_jobs(self.scheduler)  # Get existing jobs safely
        logger.debug(f"🔍 📌 Count of jobs already in the queue: {len(existing_jobs)}")

        job_id = f"scheduled_{func_name}"  # Unique job ID for scheduling

        # If job already exists, cancel it before rescheduling
        if job_id in existing_jobs:
            self.scheduler.cancel(job_id)
            logger.info(f"🔄 Rescheduling {func_name} every {interval_hours} hours.")

        # Schedule the task
        scheduled_time = datetime.utcnow() + timedelta(hours=interval_hours)
        self.scheduler.schedule(
            scheduled_time=scheduled_time,
            func=self.functions[func_name],  # Dynamically call function from registry
            args=args,
            kwargs=kwargs,
            interval=interval_hours * 3600,  # Convert hours to seconds
            repeat=None,  # Repeat indefinitely
            id=job_id
        )

        logger.info(f"✅ Scheduled {func_name} every {interval_hours} hours.")


    def save_data(self, key, value, field=None):
        """
        Save data to Redis.

        - If `field` is provided, uses a Redis hash (`hset`).
        - Otherwise, stores the entire `value` as a string (`set`).
        """
        try:
            value_json = json.dumps(value)  # Ensure value is serialized

            if field:
                self.redis_conn.hset(key, field, value_json)
                logger.info(f"💾 Saved data to Redis Hash {key}[{field}]")
            else:
                self.redis_conn.set(key, value_json)
                logger.info(f"💾 Saved data to Redis Key {key}")

        except Exception as e:
            logger.error(f"❌ Error saving data to Redis: {e}")

    def load_data(self, key, field=None):
        """
        Load data from Redis.

        - If `field` is provided, retrieves from a Redis hash (`hget`).
        - Otherwise, retrieves the entire value stored as a string (`get`).
        """
        try:
            if field:
                data = self.redis_conn.hget(key, field)
                if data:
                    return json.loads(data.decode("utf-8"))
                else:
                    return None
            else:
                data = self.redis_conn.get(key)
                if data:
                    return json.loads(data.decode("utf-8"))
                else:
                    return None
        except Exception as e:
            logger.error(f"❌ Error loading data from Redis: {e}")
            return None

    def get_all_hash_fields(self, key):
        """Retrieve all fields and values from a Redis hash."""
        data = self.redis_conn.hgetall(key)
        return {k.decode("utf-8"): json.loads(v) for k, v in data.items()} if data else {}

    def delete_data(self, key, field=None):
        """
        Deletes data from Redis.

        - If `field` is provided, deletes a field from a Redis hash (`hdel`).
        - Otherwise, deletes the entire key (`delete`).
        """
        try:
            if field:
                self.redis_conn.hdel(key, field)
                logger.info(f"🗑️ Deleted field {field} from Redis Hash {key}")
            else:
                self.redis_conn.delete(key)
                logger.info(f"🗑️ Deleted Redis Key {key}")

        except Exception as e:
            logger.error(f"❌ Error deleting data from Redis: {e}")