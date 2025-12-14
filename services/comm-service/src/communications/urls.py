from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MessageViewSet, NotificationViewSet,
    DocumentViewSet, EmailQueueViewSet
)
from .api import api

# DRF router (legacy - kept for backward compatibility during migration)
router = DefaultRouter()
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'email_queue', EmailQueueViewSet, basename='email-queue')

urlpatterns = [
    # Django Ninja API (modern - primary endpoints)
    path('', api.urls),

    # DRF API (legacy - deprecated but kept for compatibility)
    # path('api/', include(router.urls)),
]
