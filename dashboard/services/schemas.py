from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Candle(BaseModel):
    time: str  # ISO format or YYYY-MM-DD
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None


class TechnicalIndicators(BaseModel):
    sma_20: List[Optional[float]] = Field(default_factory=list)
    sma_50: List[Optional[float]] = Field(default_factory=list)
    rsi: List[Optional[float]] = Field(default_factory=list)


class MarketData(BaseModel):
    symbol: str
    provider: str
    current_price: float
    change_pct: float
    candlesticks: List[Candle]
    indicators: Optional[TechnicalIndicators] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class SearchResult(BaseModel):
    id: str
    name: str
    symbol: str
    thumb: Optional[str] = None
    platform: Optional[str] = None
    address: Optional[str] = None
    provider: str
