from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from core.auth import LoginView, MeView
from core.views import alerts, communities, dashboard, forecast_models, mark_alert_read, optimize, train_forecast_models
from weather.views import forecast, history

urlpatterns = [
    path("api/dashboard/", dashboard),
    path("api/communities/", communities),
    path("api/optimizer/run/", optimize),
    path("api/alerts/", alerts),
    path("api/alerts/<int:alert_id>/read/", mark_alert_read),
    path("api/models/<int:community_id>/", forecast_models),
    path("api/models/<int:community_id>/train/", train_forecast_models),
    path("api/auth/login/", LoginView.as_view()),
    path("api/auth/refresh/", TokenRefreshView.as_view()),
    path("api/auth/me/", MeView.as_view()),
    path("api/weather/<int:community_id>/forecast/", forecast),
    path("api/weather/<int:community_id>/history/", history),
]
