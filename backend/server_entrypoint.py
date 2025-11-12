"""
Application entrypoint for running with Gunicorn in a container.
This file creates and configures the Flask app and its extensions.
"""

from utility import logger
from run import create_app

# This is the most critical part for running with Gunicorn and eventlet.
# It must be done at the very top, before any other modules are imported.
import eventlet

eventlet.monkey_patch()

app = None

# Gunicorn can import this file multiple times. This check ensures that
# the app is only created once, preventing resource conflicts.
if not app:
    logger.info("🚀 Creating app context for server...")
    app = create_app()
