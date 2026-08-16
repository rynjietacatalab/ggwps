"""
models/user.py
---------------
Every query that touches the `users` table lives here. Passwords are
always hashed (Werkzeug) before they reach the database — the raw
password is never stored.

Accounts start with email_verified = FALSE. The only route that flips
it to TRUE is /verify-email, after a correct OTP. Login never touches
this OTP flow again once an account is verified.
"""

from werkzeug.security import generate_password_hash, check_password_hash

from models.db import get_connection


def create_user(username, email, password):
    """Returns (success: bool, message: str)."""
    username = username.strip()
    email = email.strip().lower()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            existing_username = cur.fetchone()

            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            existing_email = cur.fetchone()

            # Same person retrying registration before they ever verified —
            # let them through again (and refresh their password) instead
            # of getting stuck on "already taken".
            if (
                existing_username
                and existing_email
                and existing_username["id"] == existing_email["id"]
                and not existing_username["email_verified"]
            ):
                cur.execute(
                    "UPDATE users SET password_hash = %s WHERE id = %s",
                    (generate_password_hash(password), existing_username["id"]),
                )
                conn.commit()
                return True, "Account already exists and is awaiting verification."

            if existing_username:
                return False, "That username is already taken."

            if existing_email:
                return False, "That email is already registered."

            cur.execute(
                """
                INSERT INTO users (username, email, password_hash, email_verified)
                VALUES (%s, %s, %s, FALSE)
                """,
                (username, email, generate_password_hash(password)),
            )
        conn.commit()

    return True, "Account created."


def get_user_by_identifier(identifier):
    """Look up a user by username OR email, case-insensitive. Returns a dict or None."""
    identifier = identifier.strip().lower()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM users WHERE LOWER(username) = %s OR LOWER(email) = %s",
                (identifier, identifier),
            )
            return cur.fetchone()


def verify_password(identifier, password):
    user = get_user_by_identifier(identifier)
    if not user:
        return False
    return check_password_hash(user["password_hash"], password)


def mark_email_verified(email):
    email = email.strip().lower()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET email_verified = TRUE WHERE email = %s", (email,))
        conn.commit()
