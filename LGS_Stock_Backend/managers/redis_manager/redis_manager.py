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
import json

from utility import logger

# --- Redis Connection ---
# Use an environment variable for the URL, falling back to a default for convenience.
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379")
redis_job_conn = Redis.from_url(REDIS_URL)

# --- RQ Objects ---
# The default queue name is 'default'.
queue = Queue(connection=redis_job_conn)
scheduler = Scheduler(queue=queue, connection=redis_job_conn)

def pubsub(**kwargs):
    return redis_job_conn.pubsub(**kwargs)

def publish_worker_result(channel: str, payload: dict):
    """
    Publishes a JSON payload to a specified Redis channel using the job connection.
    This abstracts the direct Redis publish operation.
    """
    redis_job_conn.publish(channel, json.dumps(payload))

def health_check():
    try:
        redis_job_conn.ping()
        return True
    except Exception as e:
        logger.error(f"❌ Redis Health check failed: {e}")
        return False
