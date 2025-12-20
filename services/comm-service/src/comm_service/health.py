"""Health check and metrics endpoints for comm_service."""
from datetime import datetime, timezone
from django.http import JsonResponse, HttpResponse
from django.conf import settings

def health_check(_request):
    return JsonResponse({
        'status': 'ok',
        'service': settings.SERVICE_NAME,
        'time': datetime.now(timezone.utc).isoformat()
    })

def metrics_view(_request):
    metrics = [
        '# HELP service_info Service information',
        '# TYPE service_info gauge',
        f'service_info{{service="{settings.SERVICE_NAME}"}} 1',
        '# HELP service_health Service health status (1 = healthy)',
        '# TYPE service_health gauge',
        f'service_health{{service="{settings.SERVICE_NAME}"}} 1',
    ]
    return HttpResponse('\n'.join(metrics), content_type='text/plain')

