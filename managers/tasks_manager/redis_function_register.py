from managers.redis_manager import redis_manager
from managers.tasks_manager.availability_tasks import update_availability_single_card


def register_redis_function():
    # Register function so Redis can use it
    redis_manager.register_function(
        "managers.tasks_manager.availability_tasks.update_availability_single_card",
        update_availability_single_card
    )
