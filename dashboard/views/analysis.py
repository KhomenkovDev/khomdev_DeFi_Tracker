from __future__ import annotations

import json
import logging
import os

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render

from ..services.ai import generate_analysis
from ..services.cache import predict_cache_key, review_cache_key
from ..services.indicators import rsi, sma
from ..services.market_data import get_history

logger = logging.getLogger(__name__)


_MAPPED_ERRORS = {
    "quota": "API rate limit exceeded. Please wait and try again.",
    "429": "API rate limit exceeded. Please wait and try again.",
    "503": "AI service temporarily unavailable. Please try again shortly.",
    "unavailable": "AI service temporarily unavailable. Please try again shortly.",
    "api key": "No AI API key configured. Set ANTHROPIC_API_KEY in your .env file.",
}


def _map_error_message(raw: str) -> str:
    lowered = raw.lower()
    for key, msg in _MAPPED_ERRORS.items():
        if key in lowered:
            return msg
    return "An unexpected error occurred. Please try again later."


@login_required
def asset_analysis(request, asset_symbol):
    return render(request, "dashboard/analysis.html", {"asset_symbol": asset_symbol})


@login_required
def api_market_review(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    try:
        data = json.loads(request.body)
        symbol = data.get("symbol")
        period = data.get("period", "1mo")

        cache_key = review_cache_key(symbol, period)
        cached = cache.get(cache_key)
        if cached:
            return JsonResponse({"review": cached, "ai_model": "cached"})

        fetch_period = "1y" if period in ["1mo", "3mo", "6mo"] else "2y"

        try:
            final_symbol, hist = get_history(symbol, fetch_period)
        except ValueError:
            return JsonResponse({"error": "No data for this asset."}, status=404)

        close_prices = hist["Close"]
        sma_50 = sma(close_prices, 50)
        sma_20 = sma(close_prices, 20)
        rsi_val = rsi(close_prices)

        end_price = round(float(close_prices.iloc[-1]), 2)
        offset = {"1mo": 30, "3mo": 90, "6mo": 180}.get(period, 365)
        recent_hist = close_prices.tail(min(offset, len(close_prices)))
        start_price = (
            round(float(recent_hist.iloc[0]), 2) if not recent_hist.empty else end_price
        )

        prompt = f"""You are a professional crypto-asset quantitative analyst.
Analyze the digital asset {final_symbol} over the last {period} using these technical indicators:

- Price range: ${start_price} to ${end_price}
- Current price: ${end_price}
- 20-day SMA: {sma_20 if sma_20 else 'N/A'}
- 50-day SMA: {sma_50 if sma_50 else 'N/A'}
- 14-day RSI: {rsi_val if rsi_val else 'N/A'}

Write a concise market review (2 short paragraphs) covering:
trend direction, overbought/oversold signals, any Golden/Death Cross signals,
and actionable insight. Use markdown formatting."""

        review_text = generate_analysis(prompt)
        ai_model = "claude" if os.environ.get("ANTHROPIC_API_KEY") else "gemini"

        cache.set(cache_key, review_text, 60 * 60)
        return JsonResponse({"review": review_text, "ai_model": ai_model})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except ValueError as e:
        return JsonResponse({"error": _map_error_message(str(e))}, status=500)
    except Exception:
        logger.exception("Market review failed")
        return JsonResponse({"error": "An unexpected error occurred."}, status=500)


@login_required
def api_predict(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    try:
        data = json.loads(request.body)
        symbol = data.get("symbol")
        period = data.get("period", "1mo")

        cache_key = predict_cache_key(symbol, period)
        cached = cache.get(cache_key)
        if cached:
            return JsonResponse(cached)

        try:
            final_symbol, hist = get_history(symbol, "3mo")
        except ValueError:
            return JsonResponse({"error": "No data for this asset."}, status=404)

        historical_prices = [
            round(float(x), 2) for x in hist["Close"].tolist()[-30:]
        ]

        prompt = f"""You are a quantitative crypto analyst. Analyze these 30 recent close prices for {final_symbol}:
{historical_prices}

Predict the price trend for the next {period}. Be analytical about momentum,
support/resistance levels, and recent volatility.

Respond ONLY with valid JSON (no markdown, no backticks):
{{"rationale": "your 1-2 sentence reasoning", "predicted_prices": [5 float values]}}"""

        result = generate_analysis(prompt, response_json=True)

        if not isinstance(result, dict):
            return JsonResponse(
                {"error": "AI returned unexpected format."}, status=502
            )

        cache.set(cache_key, result, 60 * 60)
        return JsonResponse(result)

    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "AI returned malformed JSON. Please try again."}, status=502
        )
    except ValueError as e:
        return JsonResponse({"error": _map_error_message(str(e))}, status=500)
    except Exception:
        logger.exception("Price prediction failed")
        return JsonResponse({"error": "An unexpected error occurred."}, status=500)
