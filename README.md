# DeFi Tracker

Crypto asset watchlist with candlestick charts and LLM-generated technical commentary.

Pulls price history from yfinance (Yahoo Finance), asset search from CoinGecko, and generates market reviews via Anthropic Claude or Google Gemini.

## Status and scope

This is a personal-use dashboard. It is not suitable for production deployment without additional work (see Limitations).

yfinance is an unofficial scraper of Yahoo Finance and can break or rate-limit without warning. LLM-generated commentary is not financial advice.

## Requirements

- Python 3.12+
- (Recommended) An Anthropic API key for market reviews
- (Optional) A Google Gemini API key as a fallback AI provider
- (Optional) PostgreSQL for persistent data across restarts
- (Optional) Redis for persistent caching across instances

## Install and run

### Option A: pip (local)

```bash
# Create a virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .[dev]

# Copy and edit environment variables
cp .env.example .env
# Edit .env with your API keys

# Run migrations
python manage.py migrate

# Start the server
python manage.py runserver
```

### Option B: Docker Compose (recommended for development)

```bash
# Copy and edit environment variables
cp .env.example .env
# Edit .env with your API keys

# Start all services (Postgres, Redis, Django)
docker compose up --build
```

Open http://localhost:8000 in your browser.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | *required in prod* | Django secret key |
| `DEBUG` | `True` | Enable debug mode (dev only) |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated allowed hosts |
| `CSRF_TRUSTED_ORIGINS` | (empty in dev) | Comma-separated trusted origins |
| `DATABASE_URL` | (uses SQLite) | PostgreSQL connection string |
| `ANTHROPIC_API_KEY` | (AI disabled) | Anthropic API key for market reviews |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-20250514` | Anthropic model ID |
| `GEMINI_API_KEY` | (fallback only) | Google Gemini API key |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model ID |
| `REDIS_URL` | (uses LocMemCache) | Redis connection string |
| `APP_NAME` | `DeFi Tracker` | Application display name |
| `DJANGO_LOG_LEVEL` | `WARNING` | Django log level |

## Architecture

```
defi-tracker/
├── manage.py
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── finance_multitool/       # Django project configuration
│   ├── settings/
│   │   ├── base.py          # Shared settings
│   │   ├── dev.py           # Development overrides
│   │   └── prod.py          # Production overrides
│   └── urls.py
├── dashboard/               # Main application
│   ├── views/               # View functions grouped by domain
│   │   ├── auth.py          # Registration, login, logout
│   │   ├── dashboard.py     # Dashboard home page
│   │   ├── watchlist.py     # Watchlist toggle
│   │   ├── market.py        # Historical data, asset search
│   │   └── analysis.py      # AI market review, price predictions
│   ├── services/            # Business logic layer
│   │   ├── ai.py            # AI provider abstraction (Anthropic, Gemini)
│   │   ├── market_data.py   # yfinance wrapper
│   │   ├── indicators.py    # SMA, RSI calculations
│   │   └── cache.py         # Cache key helpers
│   ├── models.py
│   ├── urls.py
│   └── tests/
├── templates/               # Django templates
└── static/                  # Static assets (CSS)
```

## Development

### Running tests

```bash
pytest
```

### Linting and formatting

```bash
ruff check .
ruff format .
```

### Type checking

```bash
mypy dashboard/services/   # strict
mypy dashboard/             # lenient (Django views)
```

### Adding a new AI provider

1. Create a new class in `dashboard/services/ai.py` that implements the `AIProvider` protocol (a `generate` method).
2. Add the provider to `get_provider()` with the appropriate precedence.

### Adding a new market data source

1. Create a new function in `dashboard/services/market_data.py` that returns a `(symbol, DataFrame)` tuple.
2. Use it in the relevant view module under `dashboard/views/`.

## Limitations and warnings

- **yfinance fragility**: yfinance scrapes Yahoo Finance and can break without notice. Rate limits may also apply.
- **LLM hallucination**: AI-generated market reviews and price predictions are not financial advice. They may contain factual errors or nonsensical analysis.
- **Ephemeral cache**: The default LocMemCache is per-process and non-shared. For multi-instance deployments, configure a Redis backend via `REDIS_URL`.
- **Ephemeral SQLite**: SQLite on serverless platforms (Cloud Run, Heroku) resets on every container restart. Always use PostgreSQL in production.

## Screenshots

(Add a screenshot here showing the dashboard with a candlestick chart and the AI analysis page.)

## License

MIT
