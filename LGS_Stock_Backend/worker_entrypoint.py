import time
from redis import Redis
from rq import Worker, Queue
import os

from tasks.scheduler_setup import schedule_tasks
from utility import logger
from data.database.db_config import initialize_database, startup_database # <-- IMPORT DB INIT FUNCTIONS


listen = ['default']
redis_conn = Redis(host='redis', port=6379)

if __name__ == '__main__':
    # Give Redis and the scheduler a moment to be ready
    time.sleep(15)

    schedule_tasks()

    # 💡 FIX: Initialize Database Connection for the Worker
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        logger.info("Initializing database for Worker process...")
        initialize_database(database_url)
        # Note: startup_database() is usually run by the backend/scheduler to sync store data.
        # It's safest to keep it here to ensure workers have all necessary data.
        startup_database()
    else:
        logger.error("FATAL: DATABASE_URL not found. Worker cannot run tasks.")
        exit(1)

    logger.info("🎧 Worker is starting...")
    # The 'with Connection(...)' block is deprecated.
    # Pass the connection directly to the Worker.
    # Each Queue must also be initialized with a connection.
    queues = [Queue(q, connection=redis_conn) for q in listen]
    worker = Worker(queues, connection=redis_conn)
    worker.work()
