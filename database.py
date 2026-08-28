"""
database.py
SQLite persistence layer for the activation system.

Only HASHED tokens are ever stored. Raw tokens exist only transiently
in memory (generated, sent to the user, then discarded).
"""

import sqlite3
import os
import time
from contextlib import contextmanager
from typing import Optional

from config import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS activations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_hash TEXT NOT NULL UNIQUE,
    telegram_user_id INTEGER NOT NULL,
    created_at INTEGER NOT NULL,
    expires_at INTEGER NOT NULL,
    activated INTEGER NOT NULL DEFAULT 0,
    activated_at INTEGER,
    activation_ip TEXT,
    activation_user_agent TEXT,
    revoked INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_activations_token_hash
    ON activations (token_hash);

CREATE INDEX IF NOT EXISTS idx_activations_telegram_user_id
    ON activations (telegram_user_id);

CREATE INDEX IF NOT EXISTS idx_activations_expires_at
    ON activations (expires_at);
"""


def init_db():
    """Create the database file and schema if they don't already exist."""
    db_dir = os.path.dirname(config.DATABASE_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(config.DATABASE_PATH)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


@contextmanager
def get_conn():
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def create_activation(token_hash: str, telegram_user_id: int) -> int:
    """Insert a new activation record. Returns the new row id."""
    now = int(time.time())
    expires_at = now + config.TOKEN_EXPIRY_SECONDS
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO activations
                (token_hash, telegram_user_id, created_at, expires_at, activated)
            VALUES (?, ?, ?, ?, 0)
            """,
            (token_hash, telegram_user_id, now, expires_at),
        )
        return cur.lastrowid


def get_by_token_hash(token_hash: str) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT * FROM activations WHERE token_hash = ?",
            (token_hash,),
        )
        return cur.fetchone()


def mark_activated(token_hash: str, ip: str, user_agent: str) -> bool:
    now = int(time.time())
    with get_conn() as conn:
        cur = conn.execute(
            """
            UPDATE activations
            SET activated = 1, activated_at = ?, activation_ip = ?, activation_user_agent = ?
            WHERE token_hash = ? AND activated = 0 AND revoked = 0
            """,
            (now, ip, user_agent, token_hash),
        )
        return cur.rowcount == 1


def revoke_token(token_hash: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE activations SET revoked = 1 WHERE token_hash = ?",
            (token_hash,),
        )
        return cur.rowcount == 1


def get_stats() -> dict:
    now = int(time.time())
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) c FROM activations").fetchone()["c"]
        used = conn.execute(
            "SELECT COUNT(*) c FROM activations WHERE activated = 1"
        ).fetchone()["c"]
        revoked = conn.execute(
            "SELECT COUNT(*) c FROM activations WHERE revoked = 1"
        ).fetchone()["c"]
        expired = conn.execute(
            "SELECT COUNT(*) c FROM activations WHERE activated = 0 AND revoked = 0 AND expires_at < ?",
            (now,),
        ).fetchone()["c"]
        active = conn.execute(
            "SELECT COUNT(*) c FROM activations WHERE activated = 0 AND revoked = 0 AND expires_at >= ?",
            (now,),
        ).fetchone()["c"]
    return {
        "total": total,
        "active": active,
        "used": used,
        "expired": expired,
        "revoked": revoked,
    }
