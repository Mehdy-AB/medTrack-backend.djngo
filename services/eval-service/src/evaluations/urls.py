"""URL configuration for evaluations app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EvaluationViewSet

router = DefaultRouter()
router.register(r'evaluations', EvaluationViewSet, basename='evaluation')

urlpatterns = router.urls
