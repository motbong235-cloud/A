"""
config.py
Centralized configuration loaded from environment variables (.env).
"""

import os
from dotenv import load_dotenv

load_dotenv()


def _get_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


class Config:
    # --- Telegram ---
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_TELEGRAM_ID: int = int(os.getenv("ADMIN_TELEGRAM_ID", "0") or 0)

    # --- Domain ---
    DOMAIN: str = os.getenv("DOMAIN", "https://mydomain.com").rstrip("/")

    # --- Token ---
    TOKEN_EXPIRY_SECONDS: int = int(os.getenv("TOKEN_EXPIRY_SECONDS", "3600") or 3600)

    # --- Database ---
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "database/activation.db")

    # --- Flask ---
    FLASK_HOST: str = os.getenv("FLASK_HOST", "0.0.0.0")
    FLASK_PORT: int = int(os.getenv("FLASK_PORT", "5000") or 5000)
    DEBUG: bool = _get_bool("DEBUG", False)

    # --- Service branding (shown on the activation page) ---
    SERVICE_NAME: str = os.getenv("SERVICE_NAME", "My Premium Service")

    @classmethod
    def validate(cls):
        """Basic sanity checks so the app fails fast with a clear message."""
        problems = []
        if not cls.BOT_TOKEN:
            problems.append("BOT_TOKEN is not set in .env")
        if cls.ADMIN_TELEGRAM_ID == 0:
            problems.append("ADMIN_TELEGRAM_ID is not set in .env")
        if not cls.DOMAIN.startswith("http"):
            problems.append("DOMAIN must start with http:// or https://")
        return problems


config = Config()
