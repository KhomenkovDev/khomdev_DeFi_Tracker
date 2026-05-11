from __future__ import annotations

import logging

import pandas as pd
import requests
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import JsonResponse
from django.conf import settings

from ..services.cache import hist_cache_key, search_cache_key
from ..services.market_data import get_history

logger = logging.getLogger(__name__)


@login_required
def get_historical_data(request):
    symbol = request.GET.get("symbol", "BTC-USD").upper()
    period = request.GET.get("period", "1mo")

    cache_key = hist_cache_key(symbol, period)
    cached_data = cache.get(cache_key)
    if cached_data:
        return JsonResponse(cached_data)

    try:
        final_symbol, hist = get_history(symbol, period)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=404)

    hist = hist.dropna()
    candlesticks = []
    seen_dates: set[str] = set()

    for date, row in hist.iterrows():
        ts = date.strftime("%Y-%m-%d")
        if ts in seen_dates:
            continue
        seen_dates.add(ts)
        candlesticks.append(
            {
                "time": ts,
                "open": float(round(row["Open"], 4)),
                "high": float(round(row["High"], 4)),
                "low": float(round(row["Low"], 4)),
                "close": float(round(row["Close"], 4)),
            }
        )

    if not candlesticks:
        return JsonResponse({"error": "No valid data points found."}, status=404)

    current_price = candlesticks[-1]["close"]
    prev_price = (
        candlesticks[-2]["close"] if len(candlesticks) > 1 else current_price
    )
    change_pct = (
        round(((current_price - prev_price) / prev_price) * 100, 2) if prev_price else 0
    )

    response_data = {
        "symbol": final_symbol,
        "candlesticks": candlesticks,
        "current_price": round(current_price, 4),
        "change_pct": change_pct,
    }
    cache.set(cache_key, response_data, 60 * 5)
    return JsonResponse(response_data)


@login_required
def api_search_assets(request):
    query = request.GET.get("q", "").strip()
    if not query:
        return JsonResponse({"results": []})

    cache_key = search_cache_key(query)
    cached_results = cache.get(cache_key)
    if cached_results:
        return JsonResponse({"results": cached_results})

    try:
        url = f"https://api.coingecko.com/api/v3/search?query={query}"
        response = requests.get(
            url, headers={"accept": "application/json"}, timeout=5
        )
        data = response.json()
        coins = data.get("coins", [])[:10]
        results = []
        for coin in coins:
            symbol = coin.get("symbol", "").upper()
            results.append(
                {
                    "id": coin.get("id"),
                    "name": coin.get("name"),
                    "symbol": symbol,
                    "thumb": coin.get("thumb"),
                    "yfinance_symbol": f"{symbol}-USD",
                }
            )
        cache.set(cache_key, results, 60 * 60)
        return JsonResponse({"results": results})
    except requests.RequestException:
        logger.exception("CoinGecko search failed for query: %s", query)
        return JsonResponse(
            {"error": "Search service temporarily unavailable."}, status=502
        )
    except Exception:
        logger.exception("Unexpected error in asset search")
        return JsonResponse({"error": "An unexpected error occurred."}, status=500)
