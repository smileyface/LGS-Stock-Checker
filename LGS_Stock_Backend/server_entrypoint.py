# This is the entrypoint for the Gunicorn server in production.
# It creates the Flask app instance. By calling create_app() without arguments,
# it allows the app to be configured via the FLASK_CONFIG environment variable,
# which is set to 'production' in the docker-compose.yml file.
from run import create_app

app = create_app()