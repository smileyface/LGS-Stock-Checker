from .redis_manager import RedisManager, REDIS_URL

# Singleton instance
redis_manager = RedisManager()


__all__ = ["redis_manager", "REDIS_URL"]