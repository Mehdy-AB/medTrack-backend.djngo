"""URL configuration for attendance app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AttendanceViewSet, AttendanceSummaryViewSet

router = DefaultRouter()
router.register(r'attendance', AttendanceViewSet, basename='attendance')
router.register(r'attendance-summary', AttendanceSummaryViewSet, basename='attendance-summary')

urlpatterns = router.urls
