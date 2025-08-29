import os
import redis

# Connection for writing data (always goes to the primary)
redis_write_client = redis.Redis(
    host=os.environ.get("REDIS_PRIMARY_HOST", "redis"),
    port=int(os.environ.get("REDIS_PRIMARY_PORT", 6379)),
    db=0,
    decode_responses=True
)

# Determine the read host. Default to the primary if no replica is specified.
read_host = os.environ.get("REDIS_REPLICA_HOST", os.environ.get("REDIS_PRIMARY_HOST", "redis"))
read_port = int(os.environ.get("REDIS_REPLICA_PORT", os.environ.get("REDIS_PRIMARY_PORT", 6379)))

# Connection for reading data (goes to the replica if available, otherwise the primary)
redis_read_client = redis.Redis(
    host=read_host,
    port=read_port,
    db=0,
    decode_responses=True
)
