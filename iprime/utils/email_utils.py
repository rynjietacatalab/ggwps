"""
utils/email_utils.py
---------------------
The ONLY file that talks to Gmail's SMTP server. If an email ever fails
to arrive, this is the one file to check.

Gmail requires an "App Password" (a 16-character code) for this, not
your normal Gmail password. See README.md for how to generate one.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import Config


def send_otp_email(recipient_email, otp_code, username="there"):
    """Returns (sent: bool, message: str)."""

    if not Config.EMAIL_ADDRESS or not Config.EMAIL_APP_PASSWORD:
        return False, (
            "EMAIL_ADDRESS / EMAIL_APP_PASSWORD are not set. "
            "Add them to your .env file (see README.md)."
        )

    subject = "Verify your iPrime account"
    body = (
        f"Hi {username},\n\n"
        f"Your iPrime verification code is: {otp_code}\n\n"
        f"It expires in {Config.OTP_EXPIRY_SECONDS // 60} minutes. Enter it on the "
        f"verification page to activate your account.\n\n"
        f"If you didn't create an iPrime account, you can ignore this email.\n"
    )

    msg = MIMEMultipart()
    msg["From"] = Config.EMAIL_ADDRESS
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(Config.EMAIL_ADDRESS, Config.EMAIL_APP_PASSWORD)
            server.send_message(msg)
        return True, "Code sent."
    except smtplib.SMTPAuthenticationError:
        return False, "Gmail rejected the login — check EMAIL_ADDRESS / EMAIL_APP_PASSWORD."
    except Exception as e:
        return False, f"Could not send email: {e}"
