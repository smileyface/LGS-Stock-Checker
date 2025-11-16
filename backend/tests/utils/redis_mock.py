import os
from unittest.mock import MagicMock, patch

# Check for a test Redis environment (e.g. Pi test server)
TEST_REDIS_URL = os.getenv("REDIS_URL", "redis://192.168.1.120:6379")

try:
    import redis

    test_redis = redis.from_url(TEST_REDIS_URL)
    test_redis.ping()
    print(f"✅ Connected to Redis at {TEST_REDIS_URL}")

    # Patch redis_conn to point to the test Redis instance
    patch(
        "managers.redis_manager.redis_manager.redis_conn", test_redis
    ).start()
    patch(
        "managers.redis_manager.redis_manager.scheduler.connection", test_redis
    ).start()

except Exception as e:
    print(
        f"⚠️ Could not connect to Redis at {TEST_REDIS_URL}. Falling back to"
        f" mock. Reason: {e}"
    )

    mock_redis = MagicMock()
    patch(
        "managers.redis_manager.redis_manager.redis_conn", mock_redis
    ).start()
    patch(
        "managers.redis_manager.redis_manager.scheduler.connection", mock_redis
    ).start()
