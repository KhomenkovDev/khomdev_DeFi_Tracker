from django.conf import settings
from django.urls import path

from .views import analysis, auth, dashboard, market, watchlist

urlpatterns = [
    path("", dashboard.dashboard_home, name="dashboard_home"),
    path("register/", auth.register, name="register"),
    path("login/", auth.login_view, name="login"),
    path("logout/", auth.logout_view, name="logout"),
    path(
        "api/historical-data/",
        market.get_historical_data,
        name="get_historical_data",
    ),
    path(
        "api/toggle-watchlist/",
        watchlist.api_toggle_watchlist,
        name="api_toggle_watchlist",
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

if settings.DEBUG:
    from .views import debug as debug_views

    urlpatterns.append(
        path("debug/auth/", debug_views.debug_auth_status, name="debug_auth_status"),
    )
