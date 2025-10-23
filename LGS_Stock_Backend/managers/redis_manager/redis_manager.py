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
_redis_job_conn = None

def get_redis_connection(decode_responses=False):
    """
    Returns a Redis connection instance, creating it if it doesn't exist.
    This lazy initialization prevents connection attempts at import time,
    making the application more resilient and easier to test.
    """
    global _redis_job_conn
    if _redis_job_conn is None:
        try:
            _redis_job_conn = Redis.from_url(REDIS_URL, decode_responses=decode_responses)
            logger.info(f"✅ Redis client created for {REDIS_URL}")
        except Exception as e:
            logger.error(f"❌ Failed to create Redis client for {REDIS_URL}: {e}")
            return None
    return _redis_job_conn

# --- RQ Objects ---
# The default queue name is 'default'.
queue = Queue(connection=get_redis_connection())
scheduler = Scheduler(queue=queue, connection=get_redis_connection())

def pubsub(**kwargs):
    return get_redis_connection().pubsub(**kwargs)

def publish_worker_result(channel: str, payload: dict):
    """
    Publishes a JSON payload to a specified Redis channel using the job connection.
    This abstracts the direct Redis publish operation.
    """
    get_redis_connection().publish(channel, json.dumps(payload))

def health_check():
    try:
        get_redis_connection().ping()
        return True
    except Exception as e:
        logger.error(f"❌ Redis Health check failed: {e}")
        return False
scheduler = Scheduler(queue=queue, connection=get_redis_connection())

