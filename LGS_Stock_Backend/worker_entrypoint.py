import eventlet

# Monkey patch at the very beginning, before any other modules are imported.
# This is crucial for compatibility with RQ's forking model.
eventlet.monkey_patch()

import os
import redis
from rq import Connection, Worker, Queue

# Import the app factory to ensure all initializations are done.
from run import create_app

# Create the Flask app. This will run all the setup code inside create_app(),
# including the registration of our Redis tasks, ensuring the worker knows about them.
app = create_app()

listen = ['default']
redis_host = os.getenv("REDIS_HOST", "redis")
redis_url = f"redis://{redis_host}:6379"

conn = redis.from_url(redis_url)

if __name__ == '__main__':
    # The 'with app.app_context()' is good practice, ensuring extensions have access
    # to the application configuration during the worker's lifespan.
    with app.app_context():
        with Connection(conn):
            queues = [Queue(name, connection=conn) for name in listen]
            worker = Worker(queues, connection=conn)
            worker.work()
