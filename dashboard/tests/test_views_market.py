from __future__ import annotations

from unittest.mock import patch

import pytest
from django.test import Client


class TestHistoricalDataView:
    URL = "/api/historical-data/"

    def test_requires_login(self, client: Client):
        response = client.get(self.URL, {"symbol": "BTC-USD"})
        assert response.status_code == 302

    @patch("dashboard.views.market.get_history")
    def test_returns_candlesticks(self, mock_get_history, logged_in_client: Client):
        import pandas as pd

        dates = pd.date_range("2026-01-01", periods=5, freq="D")
        df = pd.DataFrame(
            {
                "Open": [100, 101, 102, 103, 104],
                "High": [105, 106, 107, 108, 109],
                "Low": [95, 96, 97, 98, 99],
                "Close": [101, 102, 103, 104, 105],
            },
            index=dates,
        )
        mock_get_history.return_value = ("BTC-USD", df)

        response = logged_in_client.get(self.URL, {"symbol": "BTC-USD", "period": "5d"})
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "BTC-USD"
        assert len(data["candlesticks"]) == 5
        assert data["current_price"] == 105.0

    @patch("dashboard.views.market.get_history")
    def test_returns_404_for_unknown_symbol(
        self, mock_get_history, logged_in_client: Client
    ):
        mock_get_history.side_effect = ValueError("No data found for UNKNOWN.")
        response = logged_in_client.get(self.URL, {"symbol": "UNKNOWN"})
        assert response.status_code == 404


class TestSearchAssetsView:
    URL = "/api/search/"

    def test_requires_login(self, client: Client):
        response = client.get(self.URL, {"q": "bitcoin"})
        assert response.status_code == 302

    @patch("dashboard.views.market.requests.get")
    def test_returns_search_results(self, mock_get, logged_in_client: Client):
        mock_get.return_value.json.return_value = {
            "coins": [
                {
                    "id": "bitcoin",
                    "name": "Bitcoin",
                    "symbol": "BTC",
                    "thumb": "https://example.com/btc.png",
                }
            ]
        }
        response = logged_in_client.get(self.URL, {"q": "bitcoin"})
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1
        assert data["results"][0]["symbol"] == "BTC"

    def test_empty_query_returns_empty(self, logged_in_client: Client):
        response = logged_in_client.get(self.URL, {"q": ""})
        assert response.status_code == 200
        assert response.json() == {"results": []}
