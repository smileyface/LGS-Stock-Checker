import eventlet
eventlet.monkey_patch()

import os
import sys
from gunicorn.app.wsgiapp import run

if __name__ == '__main__':
    # This entrypoint script is used to ensure monkey-patching happens before
    # Gunicorn starts its workers. We are essentially re-creating the
    # `gunicorn` command-line executable's behavior here.
    sys.argv[0] = "gunicorn"
    sys.argv.extend(['--worker-class', 'eventlet', '-w', '4', '--bind', '0.0.0.0:5000', 'run:create_app()'])
    
    # Start Gunicorn
    run()
