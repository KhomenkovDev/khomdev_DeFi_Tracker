# Changelog

## 0.1.0 — 2026-05-11

- Split monolithic `dashboard/views.py` into modular `views/` package and `services/` layer.
- Split `finance_multitool/settings.py` into `base.py`, `dev.py`, `prod.py`.
- Replaced hardcoded secrets (`SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`) with environment variables.
- Removed `@csrf_exempt` from authenticated POST endpoints; fetch calls now send CSRF token.
- Replaced `print` error logging with `logging` module.
- Removed debug endpoint user list leak.
- Cached AI provider clients at module level.
- Centralised cache key construction.
- Replaced deprecated `unique_together` with `UniqueConstraint`.
- Removed unused dependencies (`peewee`, `beautifulsoup4`, `cryptography`, `cffi`, `curl_cffi`).
- Added `pyproject.toml` with ruff, mypy, and pytest configuration.
- Added `docker-compose.yml` for local development with Postgres and Redis.
- Added `.env.example` with documented environment variables.
- Added real test suite under `dashboard/tests/`.
- Cleaned up junk files (scratch scripts, screenshots, pycache).
- Removed hardcoded "KhomDev" branding in favour of `APP_NAME` env var.
- Bumped Docker image from Python 3.9 to 3.12.
- Removed build-time database migration from Dockerfile.
