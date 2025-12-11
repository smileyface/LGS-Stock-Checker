from rq import Queue

# Import the application factory
from app_factory import create_worker_app
from tasks.custom_worker import LGSWorker
from managers import redis_manager

listen = ["default"]

if __name__ == "__main__":
    # Create a Flask app instance. This is crucial for establishing the
    # application context that background tasks will run in, giving them
    # access to the database and other Flask extensions.
    app = create_worker_app()

    # The app context is pushed so that tasks have access to app resources.
    with app.app_context():
        queues = [
            Queue(q, connection=redis_manager.get_redis_connection())
            for q in listen
        ]
        worker = LGSWorker(queues,
                           connection=redis_manager.get_redis_connection())
        worker.work()
