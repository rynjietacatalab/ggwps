"""
config.py
---------
All settings in one place, pulled from environment variables (via a
.env file locally, or Render's Environment tab once deployed). Nothing
here should ever be a hard-coded secret.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Signs Flask's session cookie. MUST be changed for real use.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-this-key")

    # Neon Postgres connection string, exactly as shown on your Neon
    # dashboard, e.g.:
    # postgresql://user:password@ep-xxxx-pooler.us-east-2.aws.neon.tech/dbname?sslmode=require
    DATABASE_URL = os.environ.get("DATABASE_URL")

    # --- Gmail SMTP settings (used once, to verify a new account's email) ---
    # EMAIL_ADDRESS       = the Gmail account the OTP is sent FROM
    # EMAIL_APP_PASSWORD  = a 16-character Gmail "App Password" (NOT your
    #                        normal Gmail password — see README.md)
    EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
    EMAIL_APP_PASSWORD = os.environ.get("EMAIL_APP_PASSWORD")

    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587

    # How long a verification code stays valid, in seconds.
    OTP_EXPIRY_SECONDS = 5 * 60  # 5 minutes
