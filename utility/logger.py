import logging

# Custom formatter to include emojis in log levels
class EmojiFormatter(logging.Formatter):
    EMOJIS = {
        "DEBUG": "🔍",
        "INFO": "ℹ️",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "CRITICAL": "🔥"
    }

    def format(self, record):
        emoji = self.EMOJIS.get(record.levelname, "")
        record.msg = f"{emoji} {record.msg}"
        return super().format(record)

# Global Logger
logger = logging.getLogger("LGS_Stock_Checker")

if not logger.handlers:  # Prevent multiple handlers
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = EmojiFormatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

__all__ = ["logger"]
