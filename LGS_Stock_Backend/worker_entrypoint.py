import time
from redis import Redis
from rq import Worker, Queue

from tasks.scheduler_setup import schedule_tasks
from utility import logger

listen = ['default']
redis_conn = Redis(host='redis', port=6379)

if __name__ == '__main__':
    # Give Redis and the scheduler a moment to be ready
    time.sleep(15)

    schedule_tasks()

    logger.info("🎧 Worker is starting...")
    # The 'with Connection(...)' block is deprecated.
    # Pass the connection directly to the Worker.
    # Each Queue must also be initialized with a connection.
    queues = [Queue(q, connection=redis_conn) for q in listen]
    worker = Worker(queues, connection=redis_conn)
    worker.work()
