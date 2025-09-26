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
    worker = Worker(map(Queue, listen), connection=redis_conn)
    worker.work()
