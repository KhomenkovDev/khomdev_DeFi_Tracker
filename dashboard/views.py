import os
import json
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from google import genai

from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.forms import UserCreationForm
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache

from .models import UserAsset

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
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
            {'symbol': 'UNI-7083-USD', 'name': 'Uniswap'},
            {'symbol': 'LINK-USD', 'name': 'Chainlink'},
            {'symbol': 'SNX-USD', 'name': 'Synthetix'},
            {'symbol': 'MKR-USD', 'name': 'Maker'},
        ],
        'Stablecoins & Others': [
            {'symbol': 'USDC-USD', 'name': 'USDC'},
            {'symbol': 'USDT-USD', 'name': 'Tether'},
            {'symbol': 'XRP-USD', 'name': 'XRP'},
            {'symbol': 'DOGE-USD', 'name': 'Dogecoin'},
            {'symbol': 'MATIC-USD', 'name': 'Polygon'},
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
    symbol = request.GET.get('symbol', 'BTC-USD')
    period = request.GET.get('period', '1mo')
    
    # Implement LocMemCache
    cache_key = f"hist_{symbol}_{period}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return JsonResponse(cached_data)
        
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period=period)
    
    if hist.empty:
        return JsonResponse({'error': 'No data found for this symbol.'}, status=404)
        
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
            'open': float(round(row['Open'], 2)),
            'high': float(round(row['High'], 2)),
            'low': float(round(row['Low'], 2)),
            'close': float(round(row['Close'], 2))
        })
        
    if not candlesticks:
        return JsonResponse({'error': 'No valid data points found.'}, status=404)
    
    current_price = candlesticks[-1]['close']
    prev_price = candlesticks[-2]['close'] if len(candlesticks) > 1 else current_price
    change_pct = ((current_price - prev_price) / prev_price) * 100 if prev_price else 0
    change_pct = round(change_pct, 2)

    response_data = {
        'symbol': symbol,
        'candlesticks': candlesticks,
        'current_price': round(current_price, 2),
        'change_pct': change_pct
    }
    
    cache.set(cache_key, response_data, 60 * 5) # Cache for 5 minutes
    return JsonResponse(response_data)

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
            if hist is None:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=fetch_period)
                cache.set(cache_key, hist, 60*15) # Cache raw dataframe for 15m
            
            if hist.empty:
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
Here is on-chain technical data for the digital asset {symbol} over the last {period}.
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
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model_id,
                contents=prompt,
            )
            
            cache.set(gemini_cache_key, response.text, 60*60) # Cache report for 1 hour
            return JsonResponse({'review': response.text})
            
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
            
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="3mo") # Fetch 3 months of history to give AI context
            
            if hist.empty:
                return JsonResponse({'error': 'No data.'}, status=404)
                
            historical_prices = [round(x, 2) for x in hist['Close'].tolist()[-30:]] # Last 30 points
            
            prompt = f"As a stock market prediction AI, analyze these past 30 close prices for {symbol}: {historical_prices}. Predict the price trend for the next {period}. Output your reasoning in one short paragraph, followed by a list of 5 predicted future price points that follow your trend. Format strictly as JSON with keys: 'rationale' (string) and 'predicted_prices' (array of 5 floats)."
            
            api_key = os.environ.get("GEMINI_API_KEY")
            model_id = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model_id,
                contents=prompt,
            )
            
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
                
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
