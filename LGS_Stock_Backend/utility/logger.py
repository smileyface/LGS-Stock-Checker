import logging
import os
import sys

# Custom formatter to include emojis in log levels
class EmojiFormatter(logging.Formatter):
    """
    A custom log formatter that adds an emoji corresponding to the log level
    and uses a standard format string for the log message.
    """
    # Define a standard format string for consistency.
    # Example: 2023-10-27 10:30:00,123 - LGS_Stock_Checker - INFO - Log message
    FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    EMOJIS = {
        "DEBUG": "🔍",
        "INFO": "ℹ️",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "CRITICAL": "🔥",
    }

    def __init__(self, fmt=FORMAT, datefmt=None, style='%', validate=True):
        super().__init__(fmt, datefmt, style, validate)

    def format(self, record):
        # Let the parent class handle the initial formatting (timestamps, etc.)
        original_message = super().format(record)
        # Prepend the corresponding emoji to the formatted message
        emoji = self.EMOJIS.get(record.levelname, "")
        return f"{emoji} {original_message}"


def setup_logger():
    """
    Configures and returns the main application logger.
    This function is designed to be called once. The check for existing
    handlers prevents re-configuration on subsequent imports.
    """
    log = logging.getLogger("LGS_Stock_Checker")
    if log.handlers:
        return log

    log_level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    log.setLevel(log_level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(EmojiFormatter())
    log.addHandler(handler)
    return log

# Create the logger instance that will be imported by other modules
logger = setup_logger()
__all__ = ["logger"]
