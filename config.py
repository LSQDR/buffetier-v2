"""
Application configuration management.
Different configs for development, testing, and production.
"""

import os
from datetime import timedelta


class Config:
    """Base configuration"""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY')

    # Session
    SESSION_COOKIE_SECURE = True  # Set True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)

    # CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # No time limit for CSRF tokens

    # Rate Limiting
    RATELIMIT_STORAGE_URL = "memory://"
    RATELIMIT_DEFAULT = "200 per day, 100 per hour"

    # Menu Cache
    MENU_CACHE_TTL = 120  # 2 minutes


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class _RequireSecretKey:
    """Read SECRET_KEY when the production config object is loaded."""

    def __get__(self, obj, objtype=None):
        secret = os.environ.get('SECRET_KEY')
        if not secret:
            raise RuntimeError(
                'SECRET_KEY environment variable is required in production'
            )
        return secret


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SECRET_KEY = _RequireSecretKey()

    # Production should use stricter rate limits
    RATELIMIT_DEFAULT = "100 per day, 50 per hour"


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing


# Config dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
