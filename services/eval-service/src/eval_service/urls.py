"""URL configuration for eval_service."""
from django.urls import path, include
from .health import health_check, metrics_view
from django.contrib import admin
from .reports import AttendanceStatisticsView, EvaluationReportView

urlpatterns = [
    path('health', health_check, name='health'),
    path('metrics', metrics_view, name='metrics'),
    path('', include('django_prometheus.urls')),
    path('eval/', include([
        path('admin/', admin.site.urls),
        path('health', health_check, name='eval-health'),
        # Statistics and Reports
        path('statistics/attendance', AttendanceStatisticsView.as_view(), name='attendance-statistics'),
        path('reports/evaluation/<uuid:student_id>', EvaluationReportView.as_view(), name='evaluation-report'),
        # Module endpoints
        path('', include('attendance.urls')),
        path('', include('evaluations.urls')),
    ])),
]
