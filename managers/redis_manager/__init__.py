from .redis_manager import RedisManager, REDIS_URL
from .redis_function_register import register_redis_function

# Singleton instance
redis_manager = RedisManager()
register_redis_function()


__all__ = ["redis_manager", "REDIS_URL"]