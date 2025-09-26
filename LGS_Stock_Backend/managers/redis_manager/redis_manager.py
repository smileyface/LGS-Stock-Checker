import os

import redis
from rq import Queue
from rq_scheduler import Scheduler

from utility import logger

# Use an environment variable for the Redis URL, with a sensible default for Docker-based development.
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

# Centralized connection and RQ/Scheduler instances.
redis_job_conn = redis.from_url(REDIS_URL)
queue = Queue(connection=redis_job_conn)
scheduler = Scheduler(queue=queue, connection=redis_job_conn)


def get_redis_url():
    """Returns the configured Redis connection URL."""
    return REDIS_URL
