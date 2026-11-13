"""
config.py – Application configuration for Smart Notepad.
"""

import os


class Config:
    # Security
    SECRET_KEY = os.environ.get(
        "SECRET_KEY", "smart-notepad-dev-secret-key-2024-xK9#mL2$pQ7"
    )

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///notes.db"
    )
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
