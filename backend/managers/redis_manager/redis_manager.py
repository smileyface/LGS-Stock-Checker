"""
Centralized Redis connection and RQ (Redis Queue) object management.

This module creates singleton instances of the Redis connection, RQ Queue,
and RQ Scheduler. This ensures that all parts of the application (web server,
workers, scripts) interact with the same Redis-backed objects.
"""
from typing import Optional
from redis import Redis
from redis.client import PubSub
from rq import Queue
from rq_scheduler import Scheduler
import os
from schema.messaging.messages import PubSubMessage

from utility import logger

# --- Redis Connection ---
# Use an environment variable for the URL, falling back to a default
# for convenience.
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379")
_redis_connections = {}


def get_redis_connection(decode_responses=False) -> Optional[Redis]:
    """
    Returns a Redis connection instance, creating it if it doesn't
    exist for the given `decode_responses` setting. This lazy initialization
    prevents connection attempts at import time and correctly handles requests
    for connections with different decoding settings.
    """
    conn_key = str(decode_responses)

    if conn_key not in _redis_connections:
        try:
            conn = Redis.from_url(REDIS_URL, decode_responses=decode_responses)
            logger.info(
                f"✅ Redis client created for "
                f"{REDIS_URL} with decode_responses={decode_responses}"
            )
            _redis_connections[conn_key] = conn
        except Exception as e:
            logger.error(
                f"❌ Failed to create Redis client for {REDIS_URL}: {e}"
            )
            return None

    return _redis_connections.get(conn_key)


# --- RQ Objects ---
# The default queue name is 'default'.
queue = Queue(connection=get_redis_connection())
scheduler = Scheduler(queue=queue, connection=get_redis_connection())


def pubsub(**kwargs) -> Optional[PubSub]:
    """
    Returns a PubSub instance from the Redis connection.
    """
    redis_conn = get_redis_connection()
    if redis_conn is None:
        return None
    return redis_conn.pubsub(**kwargs)


def publish_pubsub(message: PubSubMessage):
    """
    Publishes a JSON payload to a specified Redis channel using
    the job connection.
    This abstracts the direct Redis publish operation.
    """
    logger.info(f"Publishing {message.payload} to {message.channel}")
    redis_conn = get_redis_connection()
    if redis_conn is None:
        return None
    redis_conn.publish(message.channel, message.payload.model_dump_json())


def health_check():
    try:
        redis_conn = get_redis_connection()
        if redis_conn is None:
            logger.error("❌ Redis connection is None")
            return False
        redis_conn.ping()
        return True
    except Exception as e:
        logger.error(f"❌ Redis Health check failed: {e}")
        return False


scheduler = Scheduler(queue=queue, connection=get_redis_connection())
