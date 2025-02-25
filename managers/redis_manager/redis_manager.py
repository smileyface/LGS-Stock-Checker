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

class RedisManager:
    """Handles Redis connections, queues, and scheduled tasks."""
    def __init__(self):
        logger.info(f"Connecting to Redis at: " + REDIS_URL)
        self.redis_conn = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        self.queue = Queue(connection=self.redis_conn)
        self.scheduler = Scheduler(queue=self.queue, connection=self.redis_conn)
        self.functions = {}  # Registry for callable functions

    def register_function(self, full_func_name, func_ref):
        """Registers a function for task queuing using its full name."""
        self.functions[full_func_name] = func_ref
        self.redis_conn.hset("registered_functions", full_func_name, "1")  # Store in Redis
        logger.info(f"🔧 Registered function: {full_func_name}")

    def queue_task(self, func_name, *args, **kwargs):
        """Queues a task by registered function name."""
        # Ensure function exists in Redis
        if not self.redis_conn.hexists("registered_functions", func_name):
            logger.error(f"❌ Attempted to queue unknown task: {func_name} (Not in Redis)")
            return

        if func_name in self.functions:
            self.queue.enqueue(self.functions[func_name], *args, **kwargs)
            logger.info(f"📌 Queued task: {func_name}")
        else:
            logger.error(f"❌ Attempted to queue unknown task: {func_name} (Not in Local Registry)")

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
        return {k: json.loads(v) for k, v in data.items()} if data else {}

    def set_hash_field(self, key, field, value):
        """Sets a field in a Redis hash."""
        self.redis_conn.hset(key, field, value)
        logger.info(f"💾 Set hash field '{field}' in key '{key}'")

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

