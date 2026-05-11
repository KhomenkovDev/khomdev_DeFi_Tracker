"""
Django settings for finance_multitool project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-3#s)9wjokv*@#z=!g*r&1m4wm%@=)+_$cgx(0g^d-x&4ln3e6u')

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*']
CSRF_TRUSTED_ORIGINS = [
    'https://khomdev-defi-tracker-87824241220.us-central1.run.app',
    'https://khomdev-finance-engine-87824241220.us-central1.run.app',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'finance_multitool.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'finance_multitool.wsgi.application'

# ── DATABASE ──────────────────────────────────────────────────────────────────
# ROOT CAUSE FIX: Cloud Run containers are ephemeral — the filesystem resets on
# every new container instance, which wipes SQLite and logs users out permanently.
#
# Solution: Use a persistent PostgreSQL database (Cloud SQL / Neon / Supabase).
# Set DATABASE_URL in your environment:
#   postgresql://user:password@host:5432/dbname
#
# For local development, DATABASE_URL can be left unset → falls back to SQLite.

DATABASE_URL = os.environ.get('DATABASE_URL', '')

if DATABASE_URL.startswith('postgresql') or DATABASE_URL.startswith('postgres'):
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=not DEBUG)
    }
else:
    # Local dev only — DO NOT deploy to Cloud Run with SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ── SESSION BACKEND ────────────────────────────────────────────────────────────
# Store sessions in the database instead of signed cookies so they persist across
# container restarts. Requires the database to be persistent (see above).
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30   # 30 days
SESSION_COOKIE_SECURE = not DEBUG          # HTTPS only in production
SESSION_COOKIE_HTTPONLY = True
SESSION_SAVE_EVERY_REQUEST = True          # Refresh session on every request

# ── CACHE ──────────────────────────────────────────────────────────────────────
# LocMemCache is per-process — fine for single-instance dev.
# For Cloud Run multi-instance, use Redis (Memorystore) instead.
REDIS_URL = os.environ.get('REDIS_URL', '')
if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'defi-tracker-cache',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard_home'
LOGOUT_REDIRECT_URL = 'login'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
