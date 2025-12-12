"""
ViewSets for COMM-SERVICE endpoints
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Message, Notification, Document, EmailQueue
from .serializers import (
    MessageSerializer, MessageCreateSerializer,
    NotificationSerializer, NotificationCreateSerializer,
    DocumentSerializer, DocumentCreateSerializer,
    EmailQueueSerializer, EmailQueueCreateSerializer
)


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Messages (internal messaging between users)

    Endpoints:
    - GET    /comm/api/messages/                - List all messages
    - POST   /comm/api/messages/                - Create message
    - GET    /comm/api/messages/{id}/           - Get specific message
    - PUT    /comm/api/messages/{id}/           - Update message
    - PATCH  /comm/api/messages/{id}/           - Partial update
    - DELETE /comm/api/messages/{id}/           - Delete message
    - GET    /comm/api/messages/sent/{sender_id}/ - Get messages sent by user
    - GET    /comm/api/messages/received/{receiver_id}/ - Get messages received by user
    - POST   /comm/api/messages/{id}/mark_read/ - Mark message as read
    """
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return MessageCreateSerializer
        return MessageSerializer

    @action(detail=False, methods=['get'], url_path='sent/(?P<sender_id>[^/.]+)')
    def sent(self, request, sender_id=None):
        """Get messages sent by a user"""
        messages = self.queryset.filter(sender_id=sender_id)
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='received/(?P<receiver_id>[^/.]+)')
    def received(self, request, receiver_id=None):
        """Get messages received by a user"""
        messages = self.queryset.filter(receiver_id=receiver_id)
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a message as read"""
        message = self.get_object()
        if not message.read_at:
            message.read_at = timezone.now()
            message.save()
        serializer = MessageSerializer(message)
        return Response(serializer.data)


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Notifications (push/email/system notifications)

    Endpoints:
    - GET    /comm/api/notifications/                  - List all notifications
    - POST   /comm/api/notifications/                  - Create notification
    - GET    /comm/api/notifications/{id}/             - Get specific notification
    - PUT    /comm/api/notifications/{id}/             - Update notification
    - PATCH  /comm/api/notifications/{id}/             - Partial update
    - DELETE /comm/api/notifications/{id}/             - Delete notification
    - GET    /comm/api/notifications/by_user/{user_id}/ - Get notifications for user
    - GET    /comm/api/notifications/by_status/{status}/ - Filter by status (pending/sent/failed)
    - POST   /comm/api/notifications/{id}/retry/       - Retry failed notification
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return NotificationCreateSerializer
        return NotificationSerializer

    @action(detail=False, methods=['get'], url_path='by_user/(?P<user_id>[^/.]+)')
    def by_user(self, request, user_id=None):
        """Get notifications for a specific user"""
        notifications = self.queryset.filter(user_id=user_id)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='by_status/(?P<status_value>[^/.]+)')
    def by_status(self, request, status_value=None):
        """Get notifications by status (pending, sent, failed)"""
        notifications = self.queryset.filter(status=status_value)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """Retry a failed notification"""
        notification = self.get_object()
        if notification.status == 'failed':
            notification.status = 'pending'
            notification.last_error = None
            notification.save()
        serializer = NotificationSerializer(notification)
        return Response(serializer.data)


class DocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Documents (file metadata, actual files stored in MinIO/S3)

    Endpoints:
    - GET    /comm/api/documents/                      - List all documents
    - POST   /comm/api/documents/                      - Create document metadata
    - GET    /comm/api/documents/{id}/                 - Get specific document
    - PUT    /comm/api/documents/{id}/                 - Update document metadata
    - PATCH  /comm/api/documents/{id}/                 - Partial update
    - DELETE /comm/api/documents/{id}/                 - Delete document metadata
    - GET    /comm/api/documents/by_owner/{owner_user_id}/ - Get documents by owner
    - GET    /comm/api/documents/by_student/{student_id}/ - Get documents by student
    - GET    /comm/api/documents/by_offer/{offer_id}/     - Get documents by offer
    """
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return DocumentCreateSerializer
        return DocumentSerializer

    @action(detail=False, methods=['get'], url_path='by_owner/(?P<owner_user_id>[^/.]+)')
    def by_owner(self, request, owner_user_id=None):
        """Get documents by owner user"""
        documents = self.queryset.filter(owner_user_id=owner_user_id)
        serializer = DocumentSerializer(documents, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='by_student/(?P<student_id>[^/.]+)')
    def by_student(self, request, student_id=None):
        """Get documents by student"""
        documents = self.queryset.filter(student_id=student_id)
        serializer = DocumentSerializer(documents, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='by_offer/(?P<offer_id>[^/.]+)')
    def by_offer(self, request, offer_id=None):
        """Get documents by offer"""
        documents = self.queryset.filter(offer_id=offer_id)
        serializer = DocumentSerializer(documents, many=True)
        return Response(serializer.data)


class EmailQueueViewSet(viewsets.ModelViewSet):
    """
    ViewSet for EmailQueue (email sending queue/task tracking)

    Endpoints:
    - GET    /comm/api/email_queue/                    - List all email queue entries
    - POST   /comm/api/email_queue/                    - Create email queue entry
    - GET    /comm/api/email_queue/{id}/               - Get specific email entry
    - PUT    /comm/api/email_queue/{id}/               - Update email entry
    - PATCH  /comm/api/email_queue/{id}/               - Partial update
    - DELETE /comm/api/email_queue/{id}/               - Delete email entry
    - GET    /comm/api/email_queue/by_status/{status}/ - Filter by status (pending/sent/failed)
    - POST   /comm/api/email_queue/{id}/retry/         - Retry failed email
    """
    queryset = EmailQueue.objects.all()
    serializer_class = EmailQueueSerializer

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return EmailQueueCreateSerializer
        return EmailQueueSerializer

    @action(detail=False, methods=['get'], url_path='by_status/(?P<status_value>[^/.]+)')
    def by_status(self, request, status_value=None):
        """Get email queue entries by status (pending, sent, failed)"""
        emails = self.queryset.filter(status=status_value)
        serializer = EmailQueueSerializer(emails, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """Retry a failed email"""
        email = self.get_object()
        if email.status == 'failed':
            email.status = 'pending'
            email.last_error = None
            email.save()
        serializer = EmailQueueSerializer(email)
        return Response(serializer.data)
