"""URL configuration for profile_service."""
from django.urls import path, include
from .health import health_check, metrics_view

urlpatterns = [
    path('health', health_check, name='health'),
    path('metrics', metrics_view, name='metrics'),
    path('', include('django_prometheus.urls')),
    path('profile/', include([
        path('health', health_check, name='profile-health'),
    ])),
]
