"""
config.py – Application configuration for Smart Notepad.
"""

import os

# Automatically load .env if present
_env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.isfile(_env_file):
    try:
        with open(_env_file, "r", encoding="utf-8") as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))
    except Exception:
        pass


class Config:
    # Security
    SECRET_KEY = os.environ.get(
        "SECRET_KEY", "smart-notepad-dev-secret-key-2024-xK9#mL2$pQ7"
    )

    # Database
    _db_url = os.environ.get("DATABASE_URL", "sqlite:///notes.db")
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_CHECK_DEFAULT = False  # Exempt API routes by default; enabled per-view

    # Debug
    DEBUG = False


class ProductionConfig(Config):
    DEBUG = False
    WTF_CSRF_ENABLED = True


class DevelopmentConfig(Config):
    DEBUG = True


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
