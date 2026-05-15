from django.conf import settings
from django.urls import path

from .views import analysis, dashboard, market

urlpatterns = [
    path("", dashboard.dashboard_home, name="dashboard_home"),
    path(
        "api/historical-data/",
        market.get_historical_data,
        name="get_historical_data",
    ),
    path(
        "analysis/<str:asset_symbol>/",
        analysis.asset_analysis,
        name="asset_analysis",
    ),
    path("api/analysis/review/", analysis.api_market_review, name="api_market_review"),
    path("api/analysis/predict/", analysis.api_predict, name="api_predict"),
    path("api/search/", market.api_search_assets, name="api_search_assets"),
]
