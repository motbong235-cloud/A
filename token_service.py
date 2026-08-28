"""
token_service.py
Secure token generation, hashing, and validation.

Raw tokens are generated with `secrets.token_urlsafe` (cryptographically
secure) and only their SHA-256 hash is ever persisted. The raw token is
handed to the user exactly once (in the Telegram message) and can never
be recovered from the database.
"""

import hashlib
import secrets
import time
from enum import Enum
from typing import Optional, Tuple

import database
from config import config


class TokenStatus(Enum):
    VALID = "valid"
    INVALID = "invalid"
    EXPIRED = "expired"
    ALREADY_USED = "already_used"
    REVOKED = "revoked"


def generate_raw_token() -> str:
    """Cryptographically secure, URL-safe token."""
    return secrets.token_urlsafe(64)


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_activation_link(telegram_user_id: int) -> Tuple[str, str]:
    """
    Generates a new token, stores its hash, and returns
    (raw_token, activation_url). The raw token is NOT stored anywhere.
    """
    raw_token = generate_raw_token()
    token_hash = hash_token(raw_token)
    database.create_activation(token_hash, telegram_user_id)
    activation_url = f"{config.DOMAIN}/activate/{raw_token}"
    return raw_token, activation_url


def check_token(raw_token: str) -> Tuple[TokenStatus, Optional[dict]]:
    """
    Validates a raw token against the database without ever needing
    to store or expose the raw value. Returns (status, row_as_dict|None).
    """
    if not raw_token or len(raw_token) < 16:
        return TokenStatus.INVALID, None

    token_hash = hash_token(raw_token)
    row = database.get_by_token_hash(token_hash)

    if row is None:
        return TokenStatus.INVALID, None

    row_dict = dict(row)

    if row_dict["revoked"]:
        return TokenStatus.REVOKED, row_dict

    if row_dict["activated"]:
        return TokenStatus.ALREADY_USED, row_dict

    if row_dict["expires_at"] < int(time.time()):
        return TokenStatus.EXPIRED, row_dict

    return TokenStatus.VALID, row_dict


def activate_token(raw_token: str, ip: str, user_agent: str) -> Tuple[TokenStatus, Optional[dict]]:
    """
    Re-validates the token and, if valid, marks it activated.
    Re-checks status atomically via the UPDATE ... WHERE clause in
    database.mark_activated to avoid race conditions (double-activation).
    """
    status, row = check_token(raw_token)
    if status != TokenStatus.VALID:
        return status, row

    token_hash = hash_token(raw_token)
    success = database.mark_activated(token_hash, ip, user_agent)

    if not success:
        # Someone else activated it in the tiny window between check and update
        return check_token(raw_token)

    # Return fresh row for confirmation screen (activation_id, etc.)
    fresh = database.get_by_token_hash(token_hash)
    return TokenStatus.VALID, dict(fresh)
