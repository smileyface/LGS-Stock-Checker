import logging
import os
import sys


# Custom formatter to include emojis in log levels
class EmojiFormatter(logging.Formatter):
    """
    A custom log formatter that replaces the textual log level (e.g., INFO)
    with a corresponding emoji.
    """

    # The format string now includes a custom field `level_emoji`
    LOG_FORMAT = "%(asctime)s - %(name)s - %(level_emoji)s - %(message)s"

    EMOJIS = {
        "DEBUG": "🐞",
        "INFO": "ℹ️",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "CRITICAL": "🔥",
    }

    def __init__(self, datefmt=None):
        # Initialize with our custom format string.
        super().__init__(self.LOG_FORMAT, datefmt)

    def format(self, record):
        # Add the custom 'level_emoji' attribute to the record.
        record.level_emoji = self.EMOJIS.get(record.levelname, "")
        # Let the parent class handle the final formatting.
        return super().format(record)


def setup_logger() -> logging.Logger:
    """
    Configures and returns the main application logger.
    This function is designed to be called once. The check for existing
    handlers prevents re-configuration on subsequent imports.
    """

    log = logging.getLogger("LGS_Stock_Checker")

    log_level_name = set_log_level(log)

    # If handlers already exist, don't add more.
    # This prevents duplicate log messages if this function is called again.
    if not log.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(EmojiFormatter())
        log.addHandler(handler)

    log.info(f"✅ Logger configured with log level: {log_level_name}")

    return log

# Create the logger instance that will be imported by other modules
logger = setup_logger()
__all__ = ["logger"]
