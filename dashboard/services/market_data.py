from __future__ import annotations

import logging
from typing import Any

import yfinance as yf

logger = logging.getLogger(__name__)


def resolve_symbol(symbol: str) -> list[str]:
    symbol = symbol.upper()
    symbols_to_try: list[str] = [symbol]
    if not symbol.endswith("-USD") and not symbol.endswith("=F"):
        symbols_to_try.append(f"{symbol}-USD")
    if "-" in symbol:
        parts = symbol.split("-")
        if len(parts) > 1:
            alt_symbol = parts[0] + "".join(parts[1:])
            if alt_symbol not in symbols_to_try:
                symbols_to_try.append(alt_symbol)
            if symbol.endswith("-USD"):
                ticker_part = "-".join(parts[:-1])
                alt_ticker = ticker_part.replace("-", "")
                alt_symbol_usd = f"{alt_ticker}-USD"
                if alt_symbol_usd not in symbols_to_try:
                    symbols_to_try.append(alt_symbol_usd)
    return symbols_to_try


def get_history(symbol: str, period: str) -> tuple[str, Any]:
    candidates = resolve_symbol(symbol)
    for s in candidates:
        try:
            ticker = yf.Ticker(s)
            hist = ticker.history(period=period)
            if not hist.empty:
                return s, hist
        except Exception:
            logger.warning("Failed to fetch data for %s", s, exc_info=True)
            continue
    raise ValueError(f"No data found for {symbol}.")
