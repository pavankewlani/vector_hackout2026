from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from core.auth import LoginView, MeView
from core.views import alerts, communities, community_request_action, community_request_convert, community_request_create, community_request_detail, community_request_status, community_requests, dashboard, forecast_models, mark_alert_read, optimize, reports, train_forecast_models
from weather.views import forecast, history, renewable

urlpatterns = [
    path("api/community-requests/", community_request_create),
    path("api/community-requests/status/", community_request_status),
    path("api/community-requests/admin/", community_requests),
    path("api/community-requests/admin/<int:request_id>/", community_request_detail),
    path("api/community-requests/admin/<int:request_id>/action/", community_request_action),
    path("api/community-requests/admin/<int:request_id>/convert/", community_request_convert),
    path("api/dashboard/", dashboard),
    path("api/communities/", communities),
    path("api/optimizer/run/", optimize),
    path("api/reports/", reports),
    path("api/alerts/", alerts),
    path("api/alerts/<int:alert_id>/read/", mark_alert_read),
    path("api/models/<int:community_id>/", forecast_models),
    path("api/models/<int:community_id>/train/", train_forecast_models),
    path("api/auth/login/", LoginView.as_view()),
    path("api/auth/refresh/", TokenRefreshView.as_view()),
    path("api/auth/me/", MeView.as_view()),
    path("api/weather/<int:community_id>/forecast/", forecast),
    path("api/weather/<int:community_id>/history/", history),
    path("api/weather/<int:community_id>/renewable/", renewable),
]
