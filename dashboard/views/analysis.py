from __future__ import annotations

import json
from datetime import date, datetime
import logging
import os
import pandas as pd

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
    "api key": "No AI API key configured. Set GEMINI_API_KEY in your .env file.",
}


def _map_error_message(raw: str) -> str:
    """
    Translates raw API or provider error strings into user-friendly messages.
    Performs a case-insensitive fuzzy match against common error patterns.
    """
    lowered = raw.lower()
    for key, msg in _MAPPED_ERRORS.items():
        if key in lowered:
            return msg
    return "An unexpected error occurred. Please try again later."


def asset_analysis(request, asset_symbol):
    """
    Renders the primary analysis dashboard for a specific asset.
    The actual data fetching is triggered via frontend AJAX to the API endpoints.
    """
    return render(request, "dashboard/analysis.html", {"asset_symbol": asset_symbol})


def api_market_review(request):
    """
    Multi-agent 'Synthesis Loop' for market analysis.
    1. Technical Agent: Analyzes patterns and indicators.
    2. Risk Agent: Analyzes volatility and liquidity.
    3. Synthesis Agent: Combines findings into a final report.
    """
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

        try:
            market_data = get_history(symbol, "1y")
        except ValueError:
            return JsonResponse({"error": "No data for this asset."}, status=404)

        closes = pd.Series([c.close for c in market_data.candlesticks])
        sma_20 = next((x for x in reversed(sma(closes, 20)) if x is not None), None)
        sma_50 = next((x for x in reversed(sma(closes, 50)) if x is not None), None)
        rsi_val = next((x for x in reversed(rsi(closes, 14)) if x is not None), None)

        # ── Step 1: Technical Analysis ──
        tech_prompt = f"""You are a Lead Technical Analyst. 
Analyze {market_data.symbol} using:
- Current Price: ${market_data.current_price}
- SMA 20: {sma_20}, SMA 50: {sma_50}
- RSI: {rsi_val}
Identify trend (Bullish/Bearish), momentum, and potential breakouts."""
        tech_analysis = generate_analysis(tech_prompt)

        # ── Step 2: Risk Assessment ──
        risk_prompt = f"""You are a Crypto Risk Manager.
Analyze the risk profile of {market_data.symbol}. 
Recent price change: {market_data.change_pct}%.
Evaluate volatility and liquidity risks based on the price data provided."""
        risk_analysis = generate_analysis(risk_prompt)

        # ── Step 3: Synthesis ──
        synthesis_prompt = f"""You are a Senior Portfolio Manager. 
Synthesize these two reports for {market_data.symbol}:

TECHNICAL ANALYSIS:
{tech_analysis}

RISK ASSESSMENT:
{risk_analysis}

Produce a final, high-fidelity 'Intelligence Report' in Markdown. 
Include sections for 'Technical Outlook', 'Risk Profile', and a final 'Actionable Insight'."""
        
        final_report = generate_analysis(synthesis_prompt)
        
        cache.set(cache_key, final_report, 60 * 60)
        return JsonResponse({"review": final_report, "ai_model": "multi-agent-synthesis"})

    except Exception:
        logger.exception("Multi-agent analysis failed")
        return JsonResponse({"error": "Intelligence synthesis failed. Please try again."}, status=500)


def api_predict(request):
    """
    Generates quantitative price predictions using LLM pattern recognition.
    Analyzes the last 30 close prices to forecast a 5-step future trend.
    """
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
            market_data = get_history(symbol, "3mo")
        except ValueError:
            return JsonResponse({"error": "No data for this asset."}, status=404)

        historical_prices = [round(c.close, 2) for c in market_data.candlesticks[-30:]]

        prompt = (
            f"You are a quantitative crypto analyst. Analyze these 30 recent "
            f"close prices for {market_data.symbol}:\n{historical_prices}\n\n"
            f"Predict the price trend for the next {period}. Be analytical about "
            f"momentum, support/resistance levels, and recent volatility.\n\n"
            f"Respond ONLY with valid JSON (no markdown, no backticks):\n"
            f'{{"rationale": "your 1-2 sentence reasoning", '
            f'"predicted_prices": [5 float values]}}'
        )

        result = generate_analysis(prompt, response_json=True)

        if not isinstance(result, dict):
            return JsonResponse({"error": "AI returned unexpected format."}, status=502)

        cache.set(cache_key, result, 60 * 60)
        return JsonResponse(result)

    except json.JSONDecodeError:
        return JsonResponse({"error": "AI returned malformed JSON. Please try again."}, status=502)
    except ValueError as e:
        return JsonResponse({"error": _map_error_message(str(e))}, status=500)
    except Exception:
        logger.exception("Price prediction failed")
        return JsonResponse({"error": "An unexpected error occurred."}, status=500)
