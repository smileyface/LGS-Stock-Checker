from typing import Callable
from managers import task_manager, user_manager
from utility import logger
from .listener import Listener


def _handle_availability_request(payload: dict):
    # Add validation to ensure the payload has the required keys.
    required_keys = ["username", "store", "card_data"]
    if not all(key in payload for key in required_keys):
        logger.error(
            f"Invalid 'availability_request' payload. Missing required keys."
            f" Payload: {payload}"
        )
        return

    # If validation passes, proceed to queue the task.
    task_manager.queue_task(
        task_manager.task_definitions.UPDATE_AVAILABILITY_SINGLE_CARD,
        payload["username"],
        payload["store"],
        payload["card_data"],
    )


def _handle_queue_all_availability_checks(payload: dict):
    username = payload.get("username")
    if not username:
        logger.error(
            f"Invalid 'queue_all_availability_checks' payload. Missing "
            f"'username'. Payload: {payload}"
        )
        return

    stores = user_manager.get_user_stores(username)
    user_cards = user_manager.load_card_list(username)

    for store in stores:
        for card in user_cards:
            # Pass the full card data model, not just the name.
            task_manager.queue_task(
                task_manager.task_definitions.UPDATE_AVAILABILITY_SINGLE_CARD,
                username,
                store.slug,
                card,
            )


HANDLER_MAP: dict[str, Callable] = {
    "availability_request":
    _handle_availability_request,
    "queue_all_availability_checks":
    _handle_queue_all_availability_checks,
}


# Create a single instance of the listener.
_listener_instance = Listener(
    service_name="Scheduler", channel="scheduler-requests"
)
for command, handler in HANDLER_MAP.items():
    _listener_instance.register_handler(command, handler)


def start_scheduler_listener(app):
    """Public function to start the singleton worker listener."""
    _listener_instance.start()
