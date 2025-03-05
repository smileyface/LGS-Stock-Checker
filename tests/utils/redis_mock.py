from unittest.mock import MagicMock, patch

# Mock Redis globally before importing any modules
mock_redis = MagicMock()
patch("redis.Redis", return_value=mock_redis).start()
patch("rq_scheduler.Scheduler", return_value=mock_redis).start()
patch("managers.redis_manager.redis_manager.redis_conn", new=mock_redis).start()