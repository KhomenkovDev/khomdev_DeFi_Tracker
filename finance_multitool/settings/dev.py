import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from .base import *  # noqa: F403, F401

DEBUG = True

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "dev-only-insecure-key-do-not-use-in-production",
)
if SECRET_KEY == "dev-only-insecure-key-do-not-use-in-production":
    logger = logging.getLogger(__name__)
    logger.warning(
        "Using an insecure SECRET_KEY for local development. "
        "Set SECRET_KEY in your .env file for production."
    )

ALLOWED_HOSTS = ["*"]

CSRF_TRUSTED_ORIGINS = []

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "defi-tracker-cache",
    }
}

SESSION_COOKIE_SECURE = False

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
