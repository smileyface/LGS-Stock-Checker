"""
Application entrypoint for running with Gunicorn in a container.
This file creates and configures the Flask app and its extensions.
"""
# This is the most critical part for running with Gunicorn and eventlet.
# It must be done at the very top, before any other modules are imported.
import eventlet
eventlet.monkey_patch()

from run import create_app

# Create the app instance using the factory.
# The factory handles all configuration, blueprint registration, and extension initialization.
app = create_app()
