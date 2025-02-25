from .redis_manager import RedisManager, REDIS_URL
import redis_function_register

# Singleton instance
redis_manager = RedisManager()


__all__ = ["redis_manager", "REDIS_URL"]