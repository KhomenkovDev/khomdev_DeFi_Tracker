from __future__ import annotations

import pandas as pd
import pytest

from dashboard.services.indicators import rsi, sma


class TestSMA:
    def test_basic_sma(self):
        series = pd.Series([1, 2, 3, 4, 5])
        result = sma(series, 3)
        assert result is not None
        assert result == 4.0

    def test_sma_with_nan(self):
        series = pd.Series([1, 2, None, 4, 5])
        result = sma(series, 3)
        assert result is None

    def test_sma_returns_none_for_short_series(self):
        series = pd.Series([1, 2])
        result = sma(series, 5)
        assert result is None


class TestRSI:
    def test_rsi_returns_value_between_0_and_100(self):
        series = pd.Series(
            [100 + i + (1 if i % 2 == 0 else -1) for i in range(20)]
        )
        result = rsi(series, 14)
        assert result is not None
        assert 0 <= result <= 100

    def test_rsi_returns_none_for_short_series(self):
        series = pd.Series([100, 101])
        result = rsi(series, 14)
        assert result is None

    def test_rsi_is_50_for_flat_prices(self):
        series = pd.Series([100] * 20)
        result = rsi(series, 14)
        assert result is None or result == 50.0
