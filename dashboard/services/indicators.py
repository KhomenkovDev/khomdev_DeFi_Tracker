from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _clean_series(series: pd.Series) -> list[float | None]:
    return [float(x) if pd.notna(x) and not np.isinf(x) else None for x in series]


def sma(series: pd.Series, window: int) -> list[float | None]:
    res = series.rolling(window=window).mean()
    return _clean_series(res)


def rsi(series: pd.Series, window: int = 14) -> list[float | None]:
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    res = 100 - (100 / (1 + rs))
    return _clean_series(res)
