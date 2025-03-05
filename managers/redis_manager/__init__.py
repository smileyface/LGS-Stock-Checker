from .redis_manager import RedisManager

# Singleton instance
redis_manager = RedisManager()


__all__ = ["redis_manager"]