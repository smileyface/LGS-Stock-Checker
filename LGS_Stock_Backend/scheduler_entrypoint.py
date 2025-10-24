import os

from run import create_app
from utility import logger
# Import the scheduler instance from the redis_manager.
from managers.redis_manager import scheduler

# Create a Flask app instance. This is crucial because the create_app
# factory imports all the necessary task modules, which registers them
# with the task manager. This makes the tasks "known" to the scheduler.
# We pass `skip_scheduler=True` to prevent an infinite loop.
logger.info("🚀 Creating app context for scheduler...")
app = create_app(skip_scheduler=True)

# Now that the app context is created and tasks are registered, start the scheduler.
# The scheduler will run in a loop, checking for jobs that are due and moving them to the queue.
logger.info("⏰ Starting RQ scheduler...")
scheduler.run()