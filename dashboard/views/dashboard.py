from __future__ import annotations

from django.shortcuts import render


def dashboard_home(request):
    # Public assets categorization
    categorized_assets = {
        "Layer 1 / Blue Chips": [
            {"symbol": "BTC-USD", "name": "Bitcoin"},
            {"symbol": "ETH-USD", "name": "Ethereum"},
            {"symbol": "SOL-USD", "name": "Solana"},
            {"symbol": "ADA-USD", "name": "Cardano"},
            {"symbol": "DOT-USD", "name": "Polkadot"},
        ],
        "DeFi & Ecosystems": [
            {"symbol": "AAVE-USD", "name": "Aave"},
            {"symbol": "UNI-USD", "name": "Uniswap"},
            {"symbol": "LINK-USD", "name": "Chainlink"},
            {"symbol": "SNX-USD", "name": "Synthetix"},
            {"symbol": "MKR-USD", "name": "Maker"},
        ],
        "Stablecoins & Others": [
            {"symbol": "USDC-USD", "name": "USDC"},
            {"symbol": "USDT-USD", "name": "Tether"},
            {"symbol": "XRP-USD", "name": "XRP"},
            {"symbol": "DOGE-USD", "name": "Dogecoin"},
            {"symbol": "AVAX-USD", "name": "Avalanche"},
        ],
    }

    # Watchlist will be handled via localStorage on the frontend
    return render(
        request,
        "dashboard/index.html",
        {
            "categorized_assets": categorized_assets,
            "starred_symbols": [],  # Frontend will populate this from localStorage
        },
    )
