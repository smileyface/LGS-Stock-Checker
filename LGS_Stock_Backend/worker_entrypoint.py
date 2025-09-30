import time
from redis import Redis
from rq import Worker, Queue
import os

from tasks.scheduler_setup import schedule_tasks
from utility import logger
from data.database.db_config import initialize_database, startup_database
from managers.redis_manager.redis_manager import redis_job_conn


listen = ["default"]

if __name__ == "__main__":
    # Give Redis and the scheduler a moment to be ready
    time.sleep(15)

    schedule_tasks()

    # 💡 FIX: Initialize Database Connection for the Worker
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        logger.info("🚀 Initializing database for Worker process...")
        initialize_database(database_url)
        startup_database()
    else:
        logger.error("💥 DATABASE_URL not found. Worker cannot run tasks.")
        exit(1)

    logger.info("🎧 Worker is starting...")
    # The 'with Connection(...)' block is deprecated.
    # Pass the connection directly to the Worker.
    # Each Queue must also be initialized with a connection.
    queues = [Queue(q, connection=redis_job_conn) for q in listen]
    worker = Worker(queues, connection=redis_job_conn)
    worker.work()
