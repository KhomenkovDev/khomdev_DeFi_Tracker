from __future__ import annotations

import logging

import requests
from django.core.cache import cache
from django.http import JsonResponse

from ..services.cache import hist_cache_key, search_cache_key
from ..services.market_data import get_history

logger = logging.getLogger(__name__)


def get_historical_data(request):
    symbol = request.GET.get("symbol", "BTC-USD").upper()
    period = request.GET.get("period", "1mo")

    cache_key = hist_cache_key(symbol, period)
    cached_data = cache.get(cache_key)
    if cached_data:
        return JsonResponse(cached_data)

    try:
        market_data = get_history(symbol, period)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=404)

    # Convert Pydantic model to dict for JSON response
    response_data = market_data.model_dump()
    
    # Cache for 5 minutes
    cache.set(cache_key, response_data, 60 * 5)
    return JsonResponse(response_data)


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
        response = requests.get(url, headers={"accept": "application/json"}, timeout=5)
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
        return JsonResponse({"error": "Search service temporarily unavailable."}, status=502)
    except Exception:
        logger.exception("Unexpected error in asset search")
        return JsonResponse({"error": "An unexpected error occurred."}, status=500)
