import json
from . import redis_manager
from utility import logger


def publish_worker_result(result_type: str, payload: dict):
    """
    Publishes a result from a worker to the 'worker-results' Redis channel.

    This function standardizes how workers send data back to the main server
    for processing (e.g., database writing).

    Args:
        result_type (str): A string identifying the type of result, which
                           determines how the server will handle it.
        payload (dict): The data payload to be sent.
    """
    try:
        message = {
            "type": result_type,
            "payload": payload
        }
        redis_manager.get_redis_connection().publish("worker-results",
                                                     json.dumps(message))
        logger.info(f"📢 Published result of type '{result_type}' to\
                     'worker-results' channel.")
    except Exception as e:
        logger.error(f"❌ Failed to publish worker result of type \
                     '{result_type}': {e}", exc_info=True)
