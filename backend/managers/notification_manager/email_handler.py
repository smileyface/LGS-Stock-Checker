import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from settings import Config
from utility import logger


# The recipient is hard-coded in settings for now.
def send_email(subject, body):
    """Sends an email notification."""
    try:
        msg = MIMEMultipart()
        msg["From"] = Config.EMAIL_SENDER
        msg["To"] = Config.EMAIL_RECIPIENT
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # Connect to the server and send the email
        server = smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT)
        server.starttls()
        server.login(Config.EMAIL_SENDER, Config.EMAIL_PASSWORD)
        server.sendmail(
            Config.EMAIL_SENDER, Config.EMAIL_RECIPIENT, msg.as_string()
        )
        server.quit()
        logger.info("✅ Email sent successfully!")
    except Exception as e:
        logger.error(f"❌ Error sending email: {e}")
