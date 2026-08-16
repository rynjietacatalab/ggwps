"""
models/db.py
-------------
The ONLY file that knows how to reach Neon. Everything else in models/
calls get_connection() from here instead of importing psycopg2 directly
— if a connection ever needs to change (pooling, retries, etc.), this
is the one place to do it.
"""

import psycopg2
from psycopg2.extras import RealDictCursor

from config import Config


def get_connection():
    """
    Opens a new connection to Neon. Every function that uses this wraps
    it in a `with` block, so the connection closes itself automatically.
    """
    if not Config.DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not set. Paste your Neon connection string "
            "into .env — see README.md for where to find it."
        )
    return psycopg2.connect(Config.DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    """
    Creates the tables this app needs if they don't already exist.
    CREATE TABLE IF NOT EXISTS is a no-op once the table is there, so
    it's safe to call this on every app startup (main.py does).
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS email_otps (
                    email VARCHAR(255) PRIMARY KEY,
                    otp_code VARCHAR(6) NOT NULL,
                    expires_at TIMESTAMPTZ NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0
                );
                """
            )
        conn.commit()
