import os
import json
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.contrib import messages
from django.views.decorators.http import require_POST

from .models import UserAsset


# ── Symbol resolution ─────────────────────────────────────────────────────────

def _get_symbols_to_try(symbol):
    symbol = symbol.upper()
    symbols_to_try = [symbol]
    if not symbol.endswith('-USD') and not symbol.endswith('=F'):
        symbols_to_try.append(f"{symbol}-USD")
    if '-' in symbol:
        parts = symbol.split('-')
        if len(parts) > 1:
            alt_symbol = parts[0] + "".join(parts[1:])
            if alt_symbol not in symbols_to_try:
                symbols_to_try.append(alt_symbol)
            if symbol.endswith('-USD'):
                ticker_part = "-".join(parts[:-1])
                alt_ticker = ticker_part.replace("-", "")
                alt_symbol_usd = f"{alt_ticker}-USD"
                if alt_symbol_usd not in symbols_to_try:
                    symbols_to_try.append(alt_symbol_usd)
    return symbols_to_try


# ── AI analysis via Claude ────────────────────────────────────────────────────

def _call_claude(prompt: str) -> str:
    """Call Anthropic Claude API. Falls back to Gemini if key not set."""
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

    if anthropic_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=anthropic_key)
            message = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            print(f"Claude API error: {e}")
            # Fall through to Gemini

    # Gemini fallback
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            from google import genai
            model_id = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
            client = genai.Client(api_key=gemini_key)
            response = client.models.generate_content(model=model_id, contents=prompt)
            return response.text or "Analysis currently unavailable."
        except Exception as e:
            print(f"Gemini fallback error: {e}")
            raise

    raise ValueError("No AI API key configured. Set ANTHROPIC_API_KEY in your .env file.")


# ── AUTH VIEWS ────────────────────────────────────────────────────────────────
# THE LOGIN BUG EXPLAINED:
# The original app used SQLite on an ephemeral Cloud Run container filesystem.
# Every new container instance starts with a fresh empty database, so users
# registered in one instance cannot be found by another. The fix is:
# 1. Use a persistent PostgreSQL database (set DATABASE_URL in .env)
# 2. Use database-backed sessions (SESSION_ENGINE = 'db' in settings)
# 3. Use Django's built-in authenticate() to verify credentials properly
# 4. Show clear error messages when login fails

def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard_home')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in immediately after registration
            login(request, user)
            messages.success(request, f"Welcome, {user.username}! Your account has been created.")
            return redirect('dashboard_home')
        else:
            # Surface form errors clearly
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}" if field != '__all__' else error)
    else:
        form = UserCreationForm()

    return render(request, 'registration/register.html', {'form': form})


def login_view(request):
    """
    Custom login view that uses authenticate() correctly and gives clear
    error messages instead of silently failing.
    """
    if request.user.is_authenticated:
        return redirect('dashboard_home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            messages.error(request, "Please enter both your username and password.")
            return render(request, 'registration/login.html', {'username': username})

        # authenticate() checks the hashed password against the database
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            # Honour ?next= redirect
            next_url = request.GET.get('next') or request.POST.get('next') or 'dashboard_home'
            return redirect(next_url)
        else:
            # Give a specific, actionable error message
            from django.contrib.auth.models import User
            if User.objects.filter(username=username).exists():
                messages.error(request, "Incorrect password. Please try again.")
            else:
                messages.error(request, f"No account found for '{username}'. Please register first.")

    return render(request, 'registration/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')


# ── DASHBOARD ─────────────────────────────────────────────────────────────────

@login_required
def dashboard_home(request):
    user_assets = UserAsset.objects.filter(user=request.user)
    watchlist_items = [{'symbol': ua.symbol, 'name': ua.name or ua.symbol} for ua in user_assets]

    categorized_assets = {}
    if watchlist_items:
        categorized_assets['Your Watchlist'] = watchlist_items

    categorized_assets.update({
        'Layer 1 / Blue Chips': [
            {'symbol': 'BTC-USD', 'name': 'Bitcoin'},
            {'symbol': 'ETH-USD', 'name': 'Ethereum'},
            {'symbol': 'SOL-USD', 'name': 'Solana'},
            {'symbol': 'ADA-USD', 'name': 'Cardano'},
            {'symbol': 'DOT-USD', 'name': 'Polkadot'},
        ],
        'DeFi & Ecosystems': [
            {'symbol': 'AAVE-USD', 'name': 'Aave'},
            {'symbol': 'UNI7083-USD', 'name': 'Uniswap'},
            {'symbol': 'LINK-USD', 'name': 'Chainlink'},
            {'symbol': 'SNX-USD', 'name': 'Synthetix'},
            {'symbol': 'MKR-USD', 'name': 'Maker'},
        ],
        'Stablecoins & Others': [
            {'symbol': 'USDC-USD', 'name': 'USDC'},
            {'symbol': 'USDT-USD', 'name': 'Tether'},
            {'symbol': 'XRP-USD', 'name': 'XRP'},
            {'symbol': 'DOGE-USD', 'name': 'Dogecoin'},
            {'symbol': 'AVAX-USD', 'name': 'Avalanche'},
        ],
    })

    starred_symbols = [ua.symbol for ua in user_assets]
    return render(request, 'dashboard/index.html', {
        'categorized_assets': categorized_assets,
        'starred_symbols': starred_symbols,
    })


# ── API VIEWS ─────────────────────────────────────────────────────────────────

@login_required
@csrf_exempt
def api_toggle_watchlist(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            symbol = data.get('symbol')
            name = data.get('name', symbol)
            asset, created = UserAsset.objects.get_or_create(user=request.user, symbol=symbol)
            if not created:
                asset.delete()
                return JsonResponse({'status': 'removed', 'symbol': symbol})
            else:
                asset.name = name
                asset.save()
                return JsonResponse({'status': 'added', 'symbol': symbol})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def get_historical_data(request):
    symbol = request.GET.get('symbol', 'BTC-USD').upper()
    period = request.GET.get('period', '1mo')

    cache_key = f"hist_{symbol}_{period}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return JsonResponse(cached_data)

    hist = None
    final_symbol = symbol

    for s in _get_symbols_to_try(symbol):
        try:
            ticker = yf.Ticker(s)
            temp_hist = ticker.history(period=period)
            if not temp_hist.empty:
                hist = temp_hist
                final_symbol = s
                break
        except Exception:
            continue

    if hist is None or hist.empty:
        return JsonResponse({'error': f'No data found for {symbol}.'}, status=404)

    hist = hist.dropna()
    candlesticks = []
    seen_dates = set()

    for date, row in hist.iterrows():
        ts = date.strftime('%Y-%m-%d')
        if ts in seen_dates:
            continue
        seen_dates.add(ts)
        candlesticks.append({
            'time': ts,
            'open': float(round(row['Open'], 4)),
            'high': float(round(row['High'], 4)),
            'low': float(round(row['Low'], 4)),
            'close': float(round(row['Close'], 4)),
        })

    if not candlesticks:
        return JsonResponse({'error': 'No valid data points found.'}, status=404)

    current_price = candlesticks[-1]['close']
    prev_price = candlesticks[-2]['close'] if len(candlesticks) > 1 else current_price
    change_pct = round(((current_price - prev_price) / prev_price) * 100, 2) if prev_price else 0

    response_data = {
        'symbol': final_symbol,
        'candlesticks': candlesticks,
        'current_price': round(current_price, 4),
        'change_pct': change_pct,
    }
    cache.set(cache_key, response_data, 60 * 5)
    return JsonResponse(response_data)


@login_required
def api_search_assets(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'results': []})

    cache_key = f"search_{query}"
    cached_results = cache.get(cache_key)
    if cached_results:
        return JsonResponse({'results': cached_results})

    try:
        url = f"https://api.coingecko.com/api/v3/search?query={query}"
        response = requests.get(url, headers={'accept': 'application/json'}, timeout=5)
        data = response.json()
        coins = data.get('coins', [])[:10]
        results = []
        for coin in coins:
            symbol = coin.get('symbol', '').upper()
            results.append({
                'id': coin.get('id'),
                'name': coin.get('name'),
                'symbol': symbol,
                'thumb': coin.get('thumb'),
                'yfinance_symbol': f"{symbol}-USD",
            })
        cache.set(cache_key, results, 60 * 60)
        return JsonResponse({'results': results})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def asset_analysis(request, asset_symbol):
    return render(request, 'dashboard/analysis.html', {'asset_symbol': asset_symbol})


@login_required
@csrf_exempt
def api_market_review(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)

    try:
        data = json.loads(request.body)
        symbol = data.get('symbol')
        period = data.get('period', '1mo')

        # Check report cache first
        cache_key = f"claude_review_{symbol}_{period}"
        cached = cache.get(cache_key)
        if cached:
            return JsonResponse({'review': cached, 'ai_model': 'cached'})

        fetch_period = "1y" if period in ["1mo", "3mo", "6mo"] else "2y"
        hist = None
        final_symbol = symbol

        for s in _get_symbols_to_try(symbol):
            ticker = yf.Ticker(s)
            hist = ticker.history(period=fetch_period)
            if not hist.empty:
                final_symbol = s
                break

        if hist is None or hist.empty:
            return JsonResponse({'error': 'No data for this asset.'}, status=404)

        close_prices = hist['Close']
        sma_50 = close_prices.rolling(window=50).mean().iloc[-1]
        sma_20 = close_prices.rolling(window=20).mean().iloc[-1]

        delta = close_prices.diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).iloc[-1]

        end_price = round(close_prices.iloc[-1], 2)
        offset = {'1mo': 30, '3mo': 90, '6mo': 180}.get(period, 365)
        recent_hist = close_prices.tail(min(offset, len(close_prices)))
        start_price = round(recent_hist.iloc[0], 2) if not recent_hist.empty else end_price

        prompt = f"""You are a professional crypto-asset quantitative analyst and DeFi specialist.
Analyze the digital asset {final_symbol} over the last {period} using these technical indicators:

- Price range: ${start_price} → ${end_price}
- Current price: ${end_price}
- 20-day SMA: ${round(sma_20, 2) if pd.notna(sma_20) else 'N/A'}
- 50-day SMA: ${round(sma_50, 2) if pd.notna(sma_50) else 'N/A'}
- 14-day RSI: {round(rsi, 2) if pd.notna(rsi) else 'N/A'}

Write a concise, high-conviction market review (2 short paragraphs) for a DeFi trader.
Cover: trend direction, overbought/oversold signals, any Golden/Death Cross signals, and actionable insight.
Use markdown formatting."""

        review_text = _call_claude(prompt)
        ai_model = "claude" if os.environ.get("ANTHROPIC_API_KEY") else "gemini"

        cache.set(cache_key, review_text, 60 * 60)
        return JsonResponse({'review': review_text, 'ai_model': ai_model})

    except Exception as e:
        error_message = str(e)
        if "quota" in error_message.lower() or "429" in error_message:
            error_message = "API rate limit exceeded. Please wait and try again."
        elif "503" in error_message or "UNAVAILABLE" in error_message:
            error_message = "AI service temporarily unavailable. Please try again shortly."
        elif "API key" in error_message:
            error_message = "No AI API key configured. Set ANTHROPIC_API_KEY in your .env file."
        return JsonResponse({'error': error_message}, status=500)


@login_required
@csrf_exempt
def api_predict(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)

    try:
        data = json.loads(request.body)
        symbol = data.get('symbol')
        period = data.get('period', '1mo')

        cache_key = f"claude_predict_{symbol}_{period}"
        cached = cache.get(cache_key)
        if cached:
            return JsonResponse(cached)

        hist = None
        final_symbol = symbol
        for s in _get_symbols_to_try(symbol):
            ticker = yf.Ticker(s)
            hist = ticker.history(period="3mo")
            if not hist.empty:
                final_symbol = s
                break

        if hist is None or hist.empty:
            return JsonResponse({'error': 'No data.'}, status=404)

        historical_prices = [round(x, 2) for x in hist['Close'].tolist()[-30:]]

        prompt = f"""You are a quantitative crypto analyst. Analyze these 30 recent close prices for {final_symbol}:
{historical_prices}

Predict the price trend for the next {period}. Be analytical about momentum, support/resistance levels, and recent volatility.

Respond ONLY with valid JSON (no markdown, no backticks):
{{"rationale": "your 1-2 sentence reasoning", "predicted_prices": [5 float values representing future price points]}}"""

        response_text = _call_claude(prompt)

        # Clean and parse JSON
        response_text = response_text.strip()
        if '```' in response_text:
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end > 0:
                response_text = response_text[start:end]

        prediction_data = json.loads(response_text)
        cache.set(cache_key, prediction_data, 60 * 60)
        return JsonResponse(prediction_data)

    except Exception as e:
        error_message = str(e)
        if "quota" in error_message.lower() or "429" in error_message:
            error_message = "API rate limit exceeded."
        return JsonResponse({'error': error_message}, status=500)


# ── Debug view (remove in production) ────────────────────────────────────────

def debug_auth_status(request):
    """Diagnostic endpoint to check auth configuration."""
    from django.contrib.auth.models import User
    from django.db import connection

    db_engine = connection.settings_dict.get('ENGINE', '')
    is_sqlite = 'sqlite' in db_engine
    users = list(User.objects.values_list('username', flat=True))

    return JsonResponse({
        'auth_status': {
            'is_authenticated': request.user.is_authenticated,
            'username': str(request.user) if request.user.is_authenticated else None,
            'session_key': request.session.session_key,
        },
        'database': {
            'engine': db_engine,
            'is_sqlite_warning': is_sqlite,
            'sqlite_warning_msg': 'SQLite on Cloud Run resets on every container restart. Set DATABASE_URL to PostgreSQL.' if is_sqlite else None,
            'user_count': len(users),
            'usernames': users,
        },
        'ai_config': {
            'claude_key_set': bool(os.environ.get('ANTHROPIC_API_KEY')),
            'gemini_key_set': bool(os.environ.get('GEMINI_API_KEY')),
            'active_ai': 'claude' if os.environ.get('ANTHROPIC_API_KEY') else ('gemini' if os.environ.get('GEMINI_API_KEY') else 'none'),
        },
    })
