"""
Application entrypoint for running with Gunicorn in a container.
This file creates and configures the Flask app and its extensions.
"""

# This is the most critical part for running with Gunicorn and eventlet.
# It must be done at the very top, before any other modules are imported.
import eventlet

eventlet.monkey_patch()

# These imports must come AFTER monkey_patching
from app_factory import create_base_app, configure_web_app
from utility import logger

# When Gunicorn starts, it will load this file and look for an 'app' variable.
# We create the fully configured web application and assign it to 'app'.

logger.info("🚀 Creating app context for server...")

# 1. Create the base application (config, logging, db)
app = create_base_app()

# 2. Apply web-specific configurations (blueprints, Socket.IO)
app = configure_web_app(app)
