import os
import redis
from utility import logger

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

try:
    # Use from_url for easy configuration and connection pooling.
    # The client is created here, but the connection is established on the first command.
    redis_conn = redis.from_url(REDIS_URL, decode_responses=True)
    logger.info(f"✅ Redis client for data layer created for {REDIS_URL}")
except Exception as e:
    logger.error(f"❌ Failed to create Redis client for {REDIS_URL}: {e}")
    redis_conn = None
