# KhomDev DeFi Tracker 🌐

Advanced Web3 portfolio monitoring, real-time crypto analytics, and AI-powered market predictions. Built with Python and integrated with CoinGecko/Binance data streams.

## Features
- **Real-Time Crypto Charts**: Interactive candlestick charts for BTC, ETH, and DeFi tokens.
- **AI Market Reviews**: High-conviction technical analysis powered by Gemini 2.5 Flash.
- **DeFi Hub**: Track your favorite Web3 assets and on-chain price action.
- **Persistent User Watchlists**: Create and manage personalized watchlists.
- **High-Performance Memory Caching**: Optimized for speed with server-side caching.
- **Web3 Ecosystem Focus**: Pre-configured categories for Layer 1s, DeFi, and Stablecoins.

## Tech Stack
- **Backend**: Python, Django
- **Frontend**: Vanilla HTML5/CSS3 (Glassmorphism), JavaScript
- **Data Source**: yfinance (simulating CoinGecko/Binance logic)
- **AI Engine**: Google Gemini 2.5 Flash
- **Database**: PostgreSQL (Production) / SQLite (Local)

## Getting Started

1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Set up your environment variables (GEMINI_API_KEY).
4. Run migrations: `python manage.py migrate`
5. Start the server: `python manage.py runserver`
