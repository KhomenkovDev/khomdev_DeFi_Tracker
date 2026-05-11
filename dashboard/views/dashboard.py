from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from ..models import UserAsset


@login_required
def dashboard_home(request):
    user_assets = UserAsset.objects.filter(user=request.user)
    watchlist_items = [
        {"symbol": ua.symbol, "name": ua.name or ua.symbol} for ua in user_assets
    ]

    categorized_assets: dict = {}
    if watchlist_items:
        categorized_assets["Your Watchlist"] = watchlist_items

    categorized_assets.update(
        {
            "Layer 1 / Blue Chips": [
                {"symbol": "BTC-USD", "name": "Bitcoin"},
                {"symbol": "ETH-USD", "name": "Ethereum"},
                {"symbol": "SOL-USD", "name": "Solana"},
                {"symbol": "ADA-USD", "name": "Cardano"},
                {"symbol": "DOT-USD", "name": "Polkadot"},
            ],
            "DeFi & Ecosystems": [
                {"symbol": "AAVE-USD", "name": "Aave"},
                {"symbol": "UNI7083-USD", "name": "Uniswap"},
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
    )

    starred_symbols = [ua.symbol for ua in user_assets]
    return render(
        request,
        "dashboard/index.html",
        {
            "categorized_assets": categorized_assets,
            "starred_symbols": starred_symbols,
        },
    )
