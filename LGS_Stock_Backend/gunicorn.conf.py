# Gunicorn configuration file

# Worker class for eventlet
worker_class = 'eventlet'

# Number of worker processes
workers = 4

# The address to bind to
bind = '0.0.0.0:5000'

# Enable logging for Gunicorn
#accesslog = '-'
#errorlog = '-'
