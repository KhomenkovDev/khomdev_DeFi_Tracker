from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def sma(series: pd.Series, window: int) -> Any | None:
    value = series.rolling(window=window).mean().iloc[-1]
    if pd.isna(value):
        return None
    return float(round(value, 2))


def rsi(series: pd.Series, window: int = 14) -> Any | None:
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    value = (100 - (100 / (1 + rs))).iloc[-1]
    if pd.isna(value) or np.isinf(value):
        return None
    return float(round(value, 2))
