import os
import redis
basedir = os.path.abspath(os.path.dirname(__file__))

LOGGING_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
LOGGER_NAME = 'LGS_Stock_Checker'
class Config:
    # Use environment variable for security in production
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-very-secret-key'

    # Configure Redis-based session storage
    SESSION_TYPE = "redis"
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = "session:"

    # --- Email Configuration (for future implementation) ---
    # It's best practice to load these from environment variables
    # to avoid committing secrets to version control.
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    EMAIL_SENDER = os.environ.get('EMAIL_SENDER')  # e.g., 'your-email@gmail.com'
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')  # Your app password
    EMAIL_RECIPIENT = os.environ.get('EMAIL_RECIPIENT')  # e.g., 'admin-email@example.com'

    @staticmethod
    def init_app(app):
        redis_host = os.getenv("REDIS_HOST", "redis")
        app.config["SESSION_REDIS"] = redis.Redis(host=redis_host, port=6379)

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False # Disable CSRF protection in tests

class ProductionConfig(Config):
    # Production specific configs go here
    pass

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
