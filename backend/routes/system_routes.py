from flask import Blueprint

from data import database
from managers import socket_manager
from managers import redis_manager
from managers import flask_manager


from utility import logger


system_bp = Blueprint("system_bp", __name__)


@system_bp.route("/api/health")
def health_check():
    """
    Health check endpoint that verifies connectivity to critical services.
    Used by Docker's healthcheck to ensure the application is fully
    operational.
    """
    try:
        # Add a guard to ensure the database has been initialized.
        if not database.get_session():
            logger.error(
                "❌ Health check failed: Database is not initialized "
                "(SessionLocal is None)."
            )
            return "Service Unavailable: DB not configured", 503

        # 1. Check Database connection
        if not database.health_check():
            logger.error("❌ Health check failed: Database connection failed.")
            return "Service Unavailable: DB connection failed", 503

        # 2. Check Redis connection
        if not redis_manager.health_check():
            logger.error("❌ Health check failed: Redis connection failed.")
            return "Service Unavailable: Redis connection failed", 503

        # 3. Check SocketIO connection
        if not socket_manager.health_check():
            logger.error("❌ Health check failed: Socket.IO connection failed.")
            return "Service Unavailable: Socket.IO connection failed", 503

        # 4. Check Flask Session OK
        if not flask_manager.health_check():
            logger.error(
                "❌ Health check failed: Flask Session connection failed."
            )
            return "Service Unavailable: Flask Session connection failed", 503

        return "OK", 200
    except Exception as e:
        # Use the application's configured logger to report the
        # health check failure.
        logger.error(
            f"❌ Health check failed: {e}", exc_info=False
        )  # exc_info=False to keep logs clean
        # Return a 503 Service Unavailable status to make the healthcheck fail.
        return "Service Unavailable", 503
