from rq.worker import Worker

from managers.socket_manager import socket_emit
from utility import logger


class LGSWorker(Worker):
    """
    A custom RQ Worker class that enhances the default shutdown behavior.

    This worker overrides the warm shutdown handler to emit a Socket.IO event
    to the frontend when a shutdown is initiated mid-job. This allows the UI
    to reflect that a background task was interrupted and may be retried.
    """

    def handle_warm_shutdown_request(self):
        """
        Handles a warm shutdown request (SIGTERM).
        """
        logger.warning(f"🚦 Warm shutdown requested for worker: {self.name}")

        job = self.get_current_job()

        if job:
            logger.info(f"Job {job.id} is currently running. Notifying client of interruption.")
            username = None
            card_name = None
            try:
                # Check if this is a card availability task, which is the only one we need to notify for.
                if job.func_name.endswith("update_availability_single_card"):
                    # Safely get username and card_name from keyword arguments or positional arguments.
                    username = job.kwargs.get("username") or (job.args[0] if job.args else None)
                    card_data = job.kwargs.get("card") or (job.args[2] if len(job.args) > 2 else {})
                    card_name = card_data.get("card_name")

                if username and card_name:
                    payload = {"card": card_name, "message": "Worker is shutting down, job will be retried."}
                    socket_emit.emit_from_worker("job_interrupted", payload, room=username)
                    logger.info(f"📡 Emitted 'job_interrupted' to room '{username}' for card '{card_name}'.")
                else:
                    logger.warning(f"Could not determine username/card_name from job '{job.id}' to emit interruption.")

            except (IndexError, AttributeError, Exception) as e:
                logger.error(f"❌ Failed to emit job interruption notification: {e}", exc_info=True)

        # After our custom logic, call the original shutdown handler.
        super().handle_warm_shutdown_request()
