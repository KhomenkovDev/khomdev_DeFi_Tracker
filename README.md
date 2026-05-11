# DeFi Tracker

Crypto asset watchlist with candlestick charts and LLM-generated technical commentary.

## Features
- Interactive candlestick charts for crypto assets.
- AI market reviews with technical indicator analysis.
- Watchlist management with CoinGecko-powered search.
- Configurable AI backend (Anthropic Claude or Google Gemini).

## Tech Stack
- **Backend**: Python, Django
- **Frontend**: HTML5/CSS3, JavaScript
- **Data Source**: yfinance (price history), CoinGecko (search)
- **AI Engine**: Anthropic Claude (primary), Google Gemini (fallback)
- **Database**: PostgreSQL (production) / SQLite (local)

## Getting Started

1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Set up your environment variables (see `.env.example`).
4. Run migrations: `python manage.py migrate`
5. Start the server: `python manage.py runserver`
