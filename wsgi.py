from LGS_Stock_Backend.run import create_app
import LGS_Stock_Backend

# This entrypoint is used by Gunicorn in the Docker container
app = create_app()