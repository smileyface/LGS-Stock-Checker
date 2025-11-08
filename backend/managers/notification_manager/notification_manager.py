from . import email_handler
from utility import logger


def send_email_notification(subject: str, body: str) -> bool:
    """
    Constructs and sends an email notification.
    This is the primary public interface for sending notifications.

    Args:
        subject: The subject of the email.
        body: The plain text body of the email.

    Returns:
        True if the email was sent successfully, False otherwise.
    """
    logger.info(f"📧 Preparing to send email notification with subject: '{subject}'")
    return email_handler.send_email(subject=subject, body=body)
