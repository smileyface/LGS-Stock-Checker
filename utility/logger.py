import logging

"""
A custom logging formatter that prepends emojis to log messages based on their severity level.

Attributes:
    EMOJIS (dict): A mapping of log level names to their corresponding emoji symbols.

Methods:
    format(record): Formats the specified log record by adding an emoji corresponding to the log level.
"""


class EmojiFormatter(logging.Formatter):
    EMOJIS = {
        "DEBUG": "🔍",
        "INFO": "ℹ️",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "CRITICAL": "🔥"
    }


    def format(self, record):
        """
            Formats a log record by prepending an emoji based on the log level.

            Args:
                record (LogRecord): The log record to be formatted.

            Returns:
                str: The formatted log message with an emoji.
        """
        emoji = self.EMOJIS.get(record.levelname, "")
        record.msg = f"{emoji} {record.msg}"
        return super().format(record)


# Global Logger
logger = logging.getLogger("LGS_Stock_Checker")

if not logger.handlers:  # Prevent multiple handlers
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    logger.addHandler(handler)

__all__ = ["logger"]
