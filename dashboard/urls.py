from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('api/historical-data/', views.get_historical_data, name='get_historical_data'),
    path('api/toggle-watchlist/', views.api_toggle_watchlist, name='api_toggle_watchlist'),
    path('analysis/<str:asset_symbol>/', views.asset_analysis, name='asset_analysis'),
    path('api/analysis/review/', views.api_market_review, name='api_market_review'),
    path('api/analysis/predict/', views.api_predict, name='api_predict'),
    path('api/search/', views.api_search_assets, name='api_search_assets'),
    path('debug/auth/', views.debug_auth_status, name='debug_auth_status'),
]
