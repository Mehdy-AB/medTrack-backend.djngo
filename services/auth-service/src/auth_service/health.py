"""
Health check and metrics endpoints for auth_service.
"""
import json
from datetime import datetime, timezone
from django.http import JsonResponse, HttpResponse
from django.conf import settings


def health_check(request):
    """
    Health check endpoint returning service status.
    """
    return JsonResponse({
        'status': 'ok',
        'service': settings.SERVICE_NAME,
        'time': datetime.now(timezone.utc).isoformat()
    })


def metrics_view(request):
    """
    Prometheus-compatible metrics endpoint.
    Basic implementation - django-prometheus handles most metrics automatically.
    """
    metrics = [
        f'# HELP service_info Service information',
        f'# TYPE service_info gauge',
        f'service_info{{service="{settings.SERVICE_NAME}"}} 1',
        f'# HELP service_health Service health status (1 = healthy)',
        f'# TYPE service_health gauge',
        f'service_health{{service="{settings.SERVICE_NAME}"}} 1',
    ]
    return HttpResponse('\n'.join(metrics), content_type='text/plain')
