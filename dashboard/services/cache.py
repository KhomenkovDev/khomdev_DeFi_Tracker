from __future__ import annotations


def hist_cache_key(symbol: str, period: str) -> str:
    return f"hist_{symbol.upper()}_{period}"


def review_cache_key(symbol: str, period: str) -> str:
    return f"review_{symbol.upper()}_{period}"


def predict_cache_key(symbol: str, period: str) -> str:
    return f"predict_{symbol.upper()}_{period}"


def search_cache_key(query: str) -> str:
    return f"search_{query.lower().strip()}"
