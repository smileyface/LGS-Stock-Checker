import time
from redis import Redis
from rq import Worker, Queue, Connection

from tasks.scheduler_setup import schedule_tasks
from utility import logger

listen = ['default']
redis_conn = Redis(host='redis', port=6379)

if __name__ == '__main__':
    # Give Redis and the scheduler a moment to be ready
    time.sleep(15)

    schedule_tasks()

    logger.info("🎧 Worker is starting...")
    with Connection(redis_conn):
        worker = Worker(map(Queue, listen))
        worker.work()
