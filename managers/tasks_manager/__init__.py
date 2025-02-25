from .availability_tasks import update_availability
from .redis_function_register import register_redis_function

register_redis_function()

__all__ = ["update_availability"]
