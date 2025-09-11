import managers.redis_manager as redis_manager
from managers.availability_manager.availability_update import update_wanted_cards_availability
from managers.tasks_manager.availability_tasks import update_availability_single_card
from utility import logger


def register_redis_function():
    """
    Discovers and registers all functions that can be queued as Redis tasks.
    This should be called once on application startup to populate the Redis
    function registry.
    """
    redis_manager.register_function(
        "managers.tasks_manager.availability_tasks.update_availability_single_card",
        update_availability_single_card
    )
    logger.info("✅ Registered Redis task: update_availability_single_card")

    redis_manager.register_function(
        "update_wanted_cards_availability",
        update_wanted_cards_availability
    )
    logger.info("✅ Registered Redis task: update_wanted_cards_availability")
