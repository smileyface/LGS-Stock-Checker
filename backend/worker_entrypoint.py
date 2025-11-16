from rq import Queue

# Import the application factory
from run import create_app
from tasks.custom_worker import LGSWorker
from managers import redis_manager


listen = ["default"]

if __name__ == "__main__":
    # Create a Flask app instance. This is crucial because the create_app
    # factory imports all the necessary task modules, which registers them
    # with the task manager. This makes the tasks "known" to the RQ worker.
    # We don't need to *run* the app, just create it to load the context.
    # We pass `skip_scheduler=True` to prevent the worker from trying to
    # schedule tasks.
    app = create_app(skip_scheduler=True)

    # The app context is needed for tasks that interact with the database
    # or other Flask extensions.
    with app.app_context():
        queues = [
            Queue(q, connection=redis_manager.get_redis_connection())
            for q in listen
        ]
        worker = LGSWorker(
            queues, connection=redis_manager.get_redis_connection()
        )
        # worker.work() runs the worker in a continuous loop, listening for
        # jobs.
        worker.work()
