from __future__ import annotations

from datetime import date, datetime
import logging
from typing import Any

import pandas as pd
import yfinance as yf

from .indicators import rsi, sma
from .schemas import Candle, MarketData, TechnicalIndicators

logger = logging.getLogger(__name__)


def resolve_symbol(symbol: str) -> list[str]:
    """
    Intelligently maps common crypto symbols to yfinance-compatible tickers.
    """
    symbol = symbol.upper().strip()
    
    # Common mappings
    mappings = {
        "BTC": "BTC-USD",
        "ETH": "ETH-USD",
        "SOL": "SOL-USD",
        "UNI": "UNI-USD",
        "AAVE": "AAVE-USD",
        "LINK": "LINK-USD",
    }
    
    if symbol in mappings:
        return [mappings[symbol]]
        
    symbols_to_try: list[str] = [symbol]
    
    if not symbol.endswith("-USD") and not symbol.endswith("=F"):
        symbols_to_try.append(f"{symbol}-USD")
        
    if "-" in symbol:
        parts = symbol.split("-")
        if len(parts) > 1:
            # Try removing the dash (e.g. WBTC-USD -> WBTCUSD)
            alt_symbol = parts[0] + "".join(parts[1:])
            if alt_symbol not in symbols_to_try:
                symbols_to_try.append(alt_symbol)
    
    return symbols_to_try


import httpx

class GeckoTerminalProvider:
    """
    Fetches DeFi-native data from GeckoTerminal and DexScreener.
    """
    BASE_URL = "https://api.geckoterminal.com/api/v2"
    DEX_SCREENER_URL = "https://api.dexscreener.com/latest/dex/search"

    def get_market_data(self, symbol: str, period: str = "1mo") -> MarketData | None:
        try:
            # 1. Search for the best pair on DexScreener
            with httpx.Client(timeout=10.0) as client:
                search_res = client.get(f"{self.DEX_SCREENER_URL}?q={symbol}")
                search_res.raise_for_status()
                data = search_res.json()
                
                pairs = data.get("pairs", [])
                if not pairs:
                    return None
                
                # Sort by liquidity or volume to find the best pair
                # For now, just take the first one
                best_pair = pairs[0]
                network = best_pair["chainId"]
                pool_address = best_pair["pairAddress"]
                token_symbol = best_pair["baseToken"]["symbol"]
                
                # 2. Get OHLCV from GeckoTerminal
                # Map periods to GeckoTerminal timeframes
                # options: day, hour, minute
                timeframe = "day"
                aggregate = 1
                limit = 100
                
                ohlcv_url = f"{self.BASE_URL}/networks/{network}/pools/{pool_address}/ohlcv/{timeframe}"
                params = {"aggregate": aggregate, "limit": limit}
                
                ohlcv_res = client.get(ohlcv_url, params=params)
                if ohlcv_res.status_code != 200:
                    logger.warning("GeckoTerminal failed for %s on %s", pool_address, network)
                    return None
                
                ohlcv_data = ohlcv_res.json()
                data_points = ohlcv_data.get("data", {}).get("attributes", {}).get("ohlcv_list", [])
                
                if not data_points:
                    return None
                
                # GeckoTerminal returns [timestamp, open, high, low, close, volume]
                # Usually sorted newest first, we want oldest first
                data_points.reverse()
                
                candlesticks = []
                for p in data_points:
                    dt = datetime.fromtimestamp(p[0])
                    candlesticks.append(
                        Candle(
                            time=dt.strftime("%Y-%m-%d"),
                            open=float(p[1]),
                            high=float(p[2]),
                            low=float(p[3]),
                            close=float(p[4]),
                            volume=float(p[5]),
                        )
                    )
                
                current_price = float(best_pair["priceUsd"])
                change_pct = float(best_pair.get("priceChange", {}).get("h24", 0))

                # Compute Indicators
                closes = pd.Series([c.close for c in candlesticks])
                indicators = TechnicalIndicators(
                    sma_20=sma(closes, 20),
                    sma_50=sma(closes, 50),
                    rsi=rsi(closes, 14),
                )

                return MarketData(
                    symbol=token_symbol,
                    provider="geckoterminal",
                    current_price=round(current_price, 6),
                    change_pct=round(change_pct, 2),
                    candlesticks=candlesticks,
                    indicators=indicators,
                )
        except Exception as e:
            logger.error("DeFi provider failed for %s: %s", symbol, str(e))
            return None


def get_history(symbol: str, period: str = "1mo") -> MarketData:
    """
    Fetches historical data using multiple providers.
    1. Tries yfinance (best for Blue Chips/Traditional)
    2. Tries GeckoTerminal (best for DeFi/On-chain)
    """
    # Try yfinance first
    candidates = resolve_symbol(symbol)
    for s in candidates:
        try:
            ticker = yf.Ticker(s)
            hist: pd.DataFrame = ticker.history(period=period)
            if not hist.empty:
                hist = hist.dropna()
                candlesticks = [
                    Candle(
                        time=date.strftime("%Y-%m-%d"),
                        open=float(row["Open"]),
                        high=float(row["High"]),
                        low=float(row["Low"]),
                        close=float(row["Close"]),
                        volume=float(row["Volume"]) if "Volume" in row else None,
                    )
                    for date, row in hist.iterrows()
                ]
                current_price = float(candlesticks[-1].close)
                prev_price = float(candlesticks[-2].close) if len(candlesticks) > 1 else current_price
                change_pct = ((current_price - prev_price) / prev_price) * 100 if prev_price else 0.0

                # Compute Indicators
                closes = pd.Series([c.close for c in candlesticks])
                indicators = TechnicalIndicators(
                    sma_20=sma(closes, 20),
                    sma_50=sma(closes, 50),
                    rsi=rsi(closes, 14),
                )

                return MarketData(
                    symbol=s,
                    provider="yfinance",
                    current_price=round(current_price, 4),
                    change_pct=round(change_pct, 2),
                    candlesticks=candlesticks,
                    indicators=indicators,
                )
        except Exception:
            continue

    # Fallback to DeFi provider
    defi_provider = GeckoTerminalProvider()
    data = defi_provider.get_market_data(symbol, period)
    if data:
        return data
            
    raise ValueError(f"No valid data found for {symbol} across any provider.")
