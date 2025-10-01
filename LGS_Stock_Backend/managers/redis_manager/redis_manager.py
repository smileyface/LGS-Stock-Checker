"""
Centralized Redis connection and RQ (Redis Queue) object management.

This module creates singleton instances of the Redis connection, RQ Queue,
and RQ Scheduler. This ensures that all parts of the application (web server,
workers, scripts) interact with the same Redis-backed objects.
"""
from redis import Redis
from rq import Queue
from rq_scheduler import Scheduler
import os

# --- Redis Connection ---
# Use an environment variable for the URL, falling back to a default for convenience.
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379")
redis_job_conn = Redis.from_url(REDIS_URL)

# --- RQ Objects ---
# The default queue name is 'default'.
queue = Queue(connection=redis_job_conn)
scheduler = Scheduler(queue=queue, connection=redis_job_conn)
