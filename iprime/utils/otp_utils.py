"""
utils/otp_utils.py
-------------------
Generates, stores, and checks the one-time code used to verify a new
account's email address. This only ever runs once per account — at
registration — never again at login.

Stored in Postgres (not memory) on purpose: a free host like Render can
spin an idle service down, and if the code lived in memory it would be
lost the moment that happens between "we emailed it" and "you typed it
in". A database row survives that.
"""

import secrets
from datetime import datetime, timedelta, timezone

from config import Config
from models.db import get_connection


def generate_otp():
    """Cryptographically-random 6-digit code, as a string (keeps leading zeros)."""
    return f"{secrets.randbelow(1_000_000):06d}"


def save_otp(email, otp_code):
    email = email.strip().lower()
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=Config.OTP_EXPIRY_SECONDS)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO email_otps (email, otp_code, expires_at, attempts)
                VALUES (%s, %s, %s, 0)
                ON CONFLICT (email)
                DO UPDATE SET otp_code = EXCLUDED.otp_code,
                              expires_at = EXCLUDED.expires_at,
                              attempts = 0
                """,
                (email, otp_code, expires_at),
            )
        conn.commit()


def verify_otp(email, submitted_otp):
    """Returns (ok: bool, message: str)."""
    email = email.strip().lower()
    submitted_otp = (submitted_otp or "").strip()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM email_otps WHERE email = %s", (email,))
            record = cur.fetchone()

            if not record:
                return False, "That code isn't valid. Request a new one."

            if datetime.now(timezone.utc) > record["expires_at"]:
                cur.execute("DELETE FROM email_otps WHERE email = %s", (email,))
                conn.commit()
                return False, "This code expired. Resend a new one."

            attempts = record["attempts"] + 1
            if attempts > 5:
                cur.execute("DELETE FROM email_otps WHERE email = %s", (email,))
                conn.commit()
                return False, "Too many attempts. Resend a new code."

            if secrets.compare_digest(submitted_otp, record["otp_code"]):
                cur.execute("DELETE FROM email_otps WHERE email = %s", (email,))
                conn.commit()
                return True, "Verified."

            cur.execute("UPDATE email_otps SET attempts = %s WHERE email = %s", (attempts, email))
            conn.commit()
            return False, "That code doesn't match. Try again."
