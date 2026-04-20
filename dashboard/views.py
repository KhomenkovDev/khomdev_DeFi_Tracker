import os
import json
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
from google import genai

from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.forms import UserCreationForm
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_message


from .models import UserAsset

def _get_symbols_to_try(symbol):
    """Generates a list of potential yfinance tickers for a given crypto symbol."""
    symbol = symbol.upper()
    symbols_to_try = [symbol]
    if not symbol.endswith('-USD') and not symbol.endswith('=F'):
        symbols_to_try.append(f"{symbol}-USD")
    
    # Also try removing hyphens (e.g. UNI-7083-USD -> UNI7083-USD)
    if '-' in symbol:
        parts = symbol.split('-')
        if len(parts) > 1:
            # Try joining parts without the first hyphen (common for yfinance crypto)
            alt_symbol = parts[0] + "".join(parts[1:])
            if alt_symbol not in symbols_to_try:
                symbols_to_try.append(alt_symbol)
            
            # If it ended in -USD, try the ticker alone without extra hyphens + -USD
            if symbol.endswith('-USD'):
                ticker_part = "-".join(parts[:-1])
                alt_ticker = ticker_part.replace("-", "")
                alt_symbol_usd = f"{alt_ticker}-USD"
                if alt_symbol_usd not in symbols_to_try:
                    symbols_to_try.append(alt_symbol_usd)
    return symbols_to_try
    
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_message(lambda m: "503" in m or "UNAVAILABLE" in m or "429" in m or "quota" in m),
    reraise=True
)
def _call_gemini(model_id, prompt, api_key):
    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing")
    
    print(f"DEBUG: Calling Gemini with model={model_id}")
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_id,
            contents=prompt,
        )
        if not response.text:
            print("DEBUG: Gemini returned an empty response (possible safety filter)")
            return "Analysis currently unavailable due to safety filters."
        return response.text
    except Exception as e:
        print(f"DEBUG: Gemini API Error: {str(e)}")
        raise e


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            print(f"DEBUG: User created: {user.username}")
            login(request, user)
            return redirect('dashboard_home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

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
        ]
    })
    
    # We pass the pure string symbols of the watchlist for the frontend JS to know if current symbol is starred
    starred_symbols = [ua.symbol for ua in user_assets]
    return render(request, 'dashboard/index.html', {
        'categorized_assets': categorized_assets,
        'starred_symbols': starred_symbols
    })

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
        except:
            continue
        
    if hist is None or hist.empty:
        return JsonResponse({'error': f'No data found for {symbol}. Try adding "-USD" (e.g., BTC-USD).'}, status=404)
        
    hist = hist.dropna()
    candlesticks = []
    seen_dates = set()
    
    for date, row in hist.iterrows():
        ts = date.strftime('%Y-%m-%d')
        if ts in seen_dates: continue
        seen_dates.add(ts)
        
        candlesticks.append({
            'time': ts,
            'open': float(round(row['Open'], 4)),
            'high': float(round(row['High'], 4)),
            'low': float(round(row['Low'], 4)),
            'close': float(round(row['Close'], 4))
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
        'change_pct': change_pct
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
        # Using CoinGecko Search API (Public / Free tier)
        url = f"https://api.coingecko.com/api/v3/search?query={query}"
        headers = {'accept': 'application/json'}
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        
        coins = data.get('coins', [])[:10] # Top 10 results
        results = []
        for coin in coins:
            symbol = coin.get('symbol').upper()
            results.append({
                'id': coin.get('id'),
                'name': coin.get('name'),
                'symbol': symbol,
                'thumb': coin.get('thumb'),
                'yfinance_symbol': f"{symbol}-USD" # Guessing yfinance symbol
            })
            
        cache.set(cache_key, results, 60 * 60) # Cache for 1 hour
        return JsonResponse({'results': results})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def asset_analysis(request, asset_symbol):
    return render(request, 'dashboard/analysis.html', {'asset_symbol': asset_symbol})

@login_required
@csrf_exempt
def api_market_review(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            symbol = data.get('symbol')
            period = data.get('period', '1mo')
            
            # Use longer period to calculate indicators properly
            fetch_period = "1y" if period in ["1mo", "3mo", "6mo"] else "2y"
            
            cache_key = f"review_data_{symbol}_{fetch_period}"
            hist = cache.get(cache_key)
            final_symbol = symbol
            if hist is None:
                for s in _get_symbols_to_try(symbol):
                    ticker = yf.Ticker(s)
                    hist = ticker.history(period=fetch_period)
                    if not hist.empty:
                        final_symbol = s
                        break
                if hist is not None and not hist.empty:
                    cache.set(cache_key, hist, 60*15) # Cache raw dataframe for 15m
            
            if hist is None or hist.empty:
                return JsonResponse({'error': 'No data for this asset.'}, status=404)
            
            # --- Technical Analysis with Pandas ---
            close_prices = hist['Close']
            
            # SMAs
            sma_50 = close_prices.rolling(window=50).mean().iloc[-1]
            sma_20 = close_prices.rolling(window=20).mean().iloc[-1]
            
            # RSI 14
            delta = close_prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            
            end_price = round(close_prices.iloc[-1], 2)
            
            # Filter the hist to the actual requested period to get the start price
            if period == '1mo': offset = 30
            elif period == '3mo': offset = 90
            elif period == '6mo': offset = 180
            else: offset = 365
            recent_hist = close_prices.tail(min(offset, len(close_prices)))
            start_price = round(recent_hist.iloc[0], 2) if not recent_hist.empty else end_price
            
            prompt = f"""You are a professional crypto-asset quantitative analyst and DeFi specialist. 
            Here is on-chain technical data for the digital asset {final_symbol} over the last {period}.
            - Price change: ${start_price} to ${end_price}
            - Current Market Price: ${end_price}
            - 20-day SMA: ${round(sma_20, 2) if pd.notna(sma_20) else 'N/A'}
            - 50-day SMA: ${round(sma_50, 2) if pd.notna(sma_50) else 'N/A'}
            - 14-day RSI: {round(rsi, 2) if pd.notna(rsi) else 'N/A'}
            
            Analyze this asset's market conditions based on these specific technical indicators. Is it overbought in the current crypto cycle? Is there a Golden Cross indicating a bullish trend? Provide a brief, high-conviction market review (1-2 paragraphs) useful for a DeFi yield farmer or crypto trader. Keep it professional and focus on Web3 market dynamics."""
            
            # Cache the Gemini call since it's identical for short times
            gemini_cache_key = f"gemini_{symbol}_{period}_review"
            cached_review = cache.get(gemini_cache_key)
            if cached_review:
                return JsonResponse({'review': cached_review})
                
            api_key = os.environ.get("GEMINI_API_KEY")
            model_id = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
            
            response_text = _call_gemini(model_id, prompt, api_key)
            
            cache.set(gemini_cache_key, response_text, 60*60) # Cache report for 1 hour
            return JsonResponse({'review': response_text})
            
        except Exception as e:
            error_message = str(e)
            if "quota" in error_message.lower() or "429" in error_message:
                error_message = "API Rate Limit Exceeded. Please check your Gemini API quota."
            elif "503" in error_message or "UNAVAILABLE" in error_message:
                error_message = "The Gemini API is temporarily unavailable (503). Please try again later."
            return JsonResponse({'error': error_message}, status=500)
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
@csrf_exempt
def api_predict(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            symbol = data.get('symbol')
            period = data.get('period', '1mo')
            
            # Check cache
            predict_cache_key = f"predict_{symbol}_{period}"
            cached_pred = cache.get(predict_cache_key)
            if cached_pred:
                return JsonResponse(cached_pred)
            
            hist = None
            final_symbol = symbol
            for s in _get_symbols_to_try(symbol):
                ticker = yf.Ticker(s)
                hist = ticker.history(period="3mo") # Fetch 3 months of history to give AI context
                if not hist.empty:
                    final_symbol = s
                    break
            
            if hist is None or hist.empty:
                return JsonResponse({'error': 'No data.'}, status=404)
                
            historical_prices = [round(x, 2) for x in hist['Close'].tolist()[-30:]] # Last 30 points
            
            prompt = f"As a stock market prediction AI, analyze these past 30 close prices for {final_symbol}: {historical_prices}. Predict the price trend for the next {period}. Output your reasoning in one short paragraph, followed by a list of 5 predicted future price points that follow your trend. Format strictly as JSON with keys: 'rationale' (string) and 'predicted_prices' (array of 5 floats)."
            
            api_key = os.environ.get("GEMINI_API_KEY")
            model_id = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
            
            response_text = _call_gemini(model_id, prompt, api_key)
            
            response_text = response_text.strip()
            # More robust JSON cleaning
            if '```' in response_text:
                # Find the first { and last }
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                if start != -1 and end != 0:
                    response_text = response_text[start:end]
                
            prediction_data = json.loads(response_text)
            
            cache.set(predict_cache_key, prediction_data, 60*60) # Cache predictions for 1 hour
            return JsonResponse(prediction_data)
        except Exception as e:
            error_message = str(e)
            if "quota" in error_message.lower() or "429" in error_message:
                error_message = "API Rate Limit Exceeded. Please check your Gemini API quota."
            elif "503" in error_message or "UNAVAILABLE" in error_message:
                error_message = "The Gemini API is temporarily unavailable (503). Please try again later."
            return JsonResponse({'error': error_message}, status=500)
    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def debug_list_users(request):
    from django.contrib.auth.models import User
    users = User.objects.all()
    user_list = [u.username for u in users]
    return JsonResponse({
        'count': len(user_list),
        'users': user_list,
        'api_key_exists': bool(os.environ.get("GEMINI_API_KEY")),
        'session_key': request.session.session_key,
        'is_authenticated': request.user.is_authenticated
    })
