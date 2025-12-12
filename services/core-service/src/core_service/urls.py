"""URL configuration for core_service."""
from django.contrib import admin
from django.urls import path, include
from .health import health_check, metrics_view

urlpatterns = [
    # Health & Metrics (root level)
    path('health', health_check, name='health'),
    path('metrics', metrics_view, name='metrics'),
    path('', include('django_prometheus.urls')),
    
    # Core API Endpoints (under /core/ prefix for Traefik)
    path('core/', include([
        path('admin/', admin.site.urls),  
        path('health', health_check, name='core-health'),
        path('offers/', include('offers.urls')),
        path('applications/', include('applications.urls')),
        path('affectations/', include('affectations.urls')),
    ])),
]
