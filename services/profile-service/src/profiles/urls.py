from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EstablishmentViewSet, ServiceViewSet,
    StudentViewSet, EncadrantViewSet,
    get_my_profile, get_dashboard_stats
)

router = DefaultRouter()
router.register(r'establishments', EstablishmentViewSet, basename='establishment')
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'students', StudentViewSet, basename='student')
router.register(r'encadrants', EncadrantViewSet, basename='encadrant')

urlpatterns = [
    path('me', get_my_profile, name='my-profile'),  # GET /profile/me
    path('dashboard-stats/', get_dashboard_stats, name='dashboard-stats'),  # GET /profile/dashboard-stats/
    path('api/', include(router.urls)),
]