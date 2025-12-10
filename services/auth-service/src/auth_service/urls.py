"""
URL configuration for auth_service.
"""
from django.urls import path, include
from .health import health_check, metrics_view

urlpatterns = [
    # Health check endpoint
    path('health', health_check, name='health'),
    
    # Metrics endpoint (Prometheus)
    path('metrics', metrics_view, name='metrics'),
    
    # Prometheus django metrics
    path('', include('django_prometheus.urls')),
    
    # Auth service specific routes will go here
    path('auth/', include([
        path('health', health_check, name='auth-health'),
    ])),
]
