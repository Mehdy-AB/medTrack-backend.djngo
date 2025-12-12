"""
Django Ninja API routers for COMM-SERVICE
Replaces DRF ViewSets while maintaining exact same endpoints
"""
import logging
from typing import List
from datetime import timedelta
from uuid import UUID
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.http import HttpRequest
from ninja import NinjaAPI, File, UploadedFile
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Message, Notification, Document, EmailQueue
from .schemas import (
    MessageCreate, MessageResponse,
    NotificationCreate, NotificationResponse,
    DocumentUploadResponse, DocumentResponse,
    EmailQueueCreate, EmailQueueResponse
)
from .service_client import AuthServiceClient, ProfileServiceClient, CoreServiceClient
from .storage import get_storage
from .events import publish_event, EventTypes, get_rabbitmq_client
import os

logger = logging.getLogger(__name__)

# Initialize RabbitMQ client on startup
try:
    get_rabbitmq_client(
        host=os.environ.get('RABBITMQ_HOST', 'rabbitmq'),
        port=int(os.environ.get('RABBITMQ_PORT', 5672)),
        user=os.environ.get('RABBITMQ_USER', 'admin'),
        password=os.environ.get('RABBITMQ_PASSWORD', 'password')
    )
    logger.info("✅ RabbitMQ client initialized for COMM-SERVICE")
except Exception as e:
    logger.warning(f"⚠️  RabbitMQ not available: {e}")

# Initialize Django Ninja API
api = NinjaAPI(
    title="COMM-SERVICE API",
    version="2.0.0",
    description="Communication service for messages, notifications, and documents with real-time WebSocket support",
    urls_namespace="communications"
)

# Get channel layer for WebSocket broadcasts
channel_layer = get_channel_layer()


# ============================================
# HELPER FUNCTIONS
# ============================================

def enrich_message(message: Message) -> dict:
    """Enrich message with user data from AUTH-SERVICE"""
    return {
        **MessageResponse.from_orm(message).dict(),
        'sender_data': AuthServiceClient.get_user_by_id(str(message.sender_id)),
        'receiver_data': AuthServiceClient.get_user_by_id(str(message.receiver_id))
    }


def enrich_notification(notification: Notification) -> dict:
    """Enrich notification with user data from AUTH-SERVICE"""
    return {
        **NotificationResponse.from_orm(notification).dict(),
        'user_data': AuthServiceClient.get_user_by_id(str(notification.user_id))
    }


def enrich_document(document: Document, include_url: bool = True) -> dict:
    """Enrich document with related data from other services"""
    data = DocumentResponse.from_orm(document).dict()

    if document.owner_user_id:
        data['owner_data'] = AuthServiceClient.get_user_by_id(str(document.owner_user_id))
    if document.student_id:
        data['student_data'] = ProfileServiceClient.get_student_by_id(str(document.student_id))
    if document.offer_id:
        data['offer_data'] = CoreServiceClient.get_offer_by_id(str(document.offer_id))
    if document.uploaded_by:
        data['uploaded_by_data'] = AuthServiceClient.get_user_by_id(str(document.uploaded_by))

    # Generate download URL
    if include_url and document.storage_path:
        storage = get_storage()
        data['download_url'] = storage.get_download_url(document.storage_path)

    return data


def enrich_email(email: EmailQueue) -> dict:
    """Enrich email with user data from AUTH-SERVICE"""
    data = EmailQueueResponse.from_orm(email).dict()
    if email.related_user_id:
        data['user_data'] = AuthServiceClient.get_user_by_id(str(email.related_user_id))
    return data


async def broadcast_to_user(user_id: str, event_type: str, data: dict):
    """Broadcast event to user's WebSocket channel"""
    try:
        await channel_layer.group_send(
            f'user_{user_id}',
            {
                'type': event_type,
                'data': data
            }
        )
        logger.info(f"Broadcast {event_type} to user {user_id}")
    except Exception as e:
        logger.error(f"Failed to broadcast to user {user_id}: {e}")


# ============================================
# MESSAGE ENDPOINTS
# ============================================

@api.get("/api/messages/", response=List[MessageResponse], tags=["Messages"])
def list_messages(request: HttpRequest):
    """Get all messages"""
    messages = Message.objects.all()
    return [enrich_message(msg) for msg in messages]


@api.post("/api/messages/", response=MessageResponse, tags=["Messages"])
def create_message(request: HttpRequest, payload: MessageCreate):
    """Create a new message and broadcast via WebSocket + RabbitMQ event"""
    message = Message.objects.create(**payload.dict())

    # Broadcast to receiver via WebSocket
    async_to_sync(broadcast_to_user)(
        str(message.receiver_id),
        'message_created',
        {
            'id': str(message.id),
            'sender_id': str(message.sender_id),
            'receiver_id': str(message.receiver_id),
            'subject': message.subject,
            'created_at': message.created_at.isoformat()
        }
    )

    # Publish RabbitMQ event
    try:
        publish_event(
            event_type=EventTypes.MESSAGE_SENT,
            payload={
                'message_id': str(message.id),
                'sender_id': str(message.sender_id),
                'receiver_id': str(message.receiver_id),
                'subject': message.subject,
                'created_at': message.created_at.isoformat()
            },
            service_name='comm-service'
        )
        logger.info(f"📤 Published message.sent event for message {message.id}")
    except Exception as e:
        logger.error(f"Failed to publish event: {e}")

    return enrich_message(message)


@api.get("/api/messages/{message_id}/", response=MessageResponse, tags=["Messages"])
def get_message(request: HttpRequest, message_id: UUID):
    """Get a specific message by ID"""
    message = get_object_or_404(Message, id=message_id)
    return enrich_message(message)


@api.get("/api/messages/sent/{sender_id}/", response=List[MessageResponse], tags=["Messages"])
def get_sent_messages(request: HttpRequest, sender_id: UUID):
    """Get all messages sent by a user"""
    messages = Message.objects.filter(sender_id=sender_id)
    return [enrich_message(msg) for msg in messages]


@api.get("/api/messages/received/{receiver_id}/", response=List[MessageResponse], tags=["Messages"])
def get_received_messages(request: HttpRequest, receiver_id: UUID):
    """Get all messages received by a user"""
    messages = Message.objects.filter(receiver_id=receiver_id)
    return [enrich_message(msg) for msg in messages]


@api.post("/api/messages/{message_id}/mark_read/", response=MessageResponse, tags=["Messages"])
def mark_message_read(request: HttpRequest, message_id: UUID):
    """Mark a message as read"""
    message = get_object_or_404(Message, id=message_id)
    if not message.read_at:
        message.read_at = timezone.now()
        message.save()
    return enrich_message(message)


@api.delete("/api/messages/{message_id}/", tags=["Messages"])
def delete_message(request: HttpRequest, message_id: UUID):
    """Delete a message"""
    message = get_object_or_404(Message, id=message_id)
    message.delete()
    return {"success": True, "message": "Message deleted"}


# ============================================
# NOTIFICATION ENDPOINTS
# ============================================

@api.get("/api/notifications/", response=List[NotificationResponse], tags=["Notifications"])
def list_notifications(request: HttpRequest):
    """Get all notifications"""
    notifications = Notification.objects.all()
    return [enrich_notification(notif) for notif in notifications]


@api.post("/api/notifications/", response=NotificationResponse, tags=["Notifications"])
def create_notification(request: HttpRequest, payload: NotificationCreate):
    """Create a new notification and broadcast via WebSocket + RabbitMQ event"""
    notification = Notification.objects.create(**payload.dict())

    # Broadcast to user via WebSocket
    async_to_sync(broadcast_to_user)(
        str(notification.user_id),
        'notification_created',
        {
            'id': str(notification.id),
            'user_id': str(notification.user_id),
            'type': notification.type,
            'title': notification.title,
            'content': notification.content,
            'created_at': notification.created_at.isoformat()
        }
    )

    # Publish RabbitMQ event
    try:
        publish_event(
            event_type=EventTypes.NOTIFICATION_CREATED,
            payload={
                'notification_id': str(notification.id),
                'user_id': str(notification.user_id),
                'type': notification.type,
                'title': notification.title,
                'content': notification.content,
                'created_at': notification.created_at.isoformat()
            },
            service_name='comm-service'
        )
        logger.info(f"📤 Published notification.created event for notification {notification.id}")
    except Exception as e:
        logger.error(f"Failed to publish event: {e}")

    return enrich_notification(notification)


@api.get("/api/notifications/{notification_id}/", response=NotificationResponse, tags=["Notifications"])
def get_notification(request: HttpRequest, notification_id: UUID):
    """Get a specific notification by ID"""
    notification = get_object_or_404(Notification, id=notification_id)
    return enrich_notification(notification)


@api.get("/api/notifications/user/{user_id}/", response=List[NotificationResponse], tags=["Notifications"])
def get_user_notifications(request: HttpRequest, user_id: UUID):
    """Get all notifications for a user"""
    notifications = Notification.objects.filter(user_id=user_id)
    return [enrich_notification(notif) for notif in notifications]


@api.delete("/api/notifications/{notification_id}/", tags=["Notifications"])
def delete_notification(request: HttpRequest, notification_id: UUID):
    """Delete a notification"""
    notification = get_object_or_404(Notification, id=notification_id)
    notification.delete()
    return {"success": True, "message": "Notification deleted"}


# ============================================
# DOCUMENT ENDPOINTS
# ============================================

@api.get("/api/documents/", response=List[DocumentResponse], tags=["Documents"])
def list_documents(request: HttpRequest):
    """Get all documents"""
    documents = Document.objects.all()
    return [enrich_document(doc) for doc in documents]


@api.post("/api/documents/upload/", response=DocumentUploadResponse, tags=["Documents"])
def upload_document(
    request: HttpRequest,
    file: UploadedFile = File(...),
    student_id: str = None,
    owner_user_id: str = None,
    uploaded_by: str = None
):
    """
    Upload a file to MinIO and create document record

    Returns document with presigned download URL (expires in 1 hour)
    """
    try:
        # Read file data
        file_data = file.read()

        # Upload to MinIO
        storage = get_storage()
        storage_path, file_size = storage.upload_file(
            file_data=file_data,
            filename=file.name,
            content_type=file.content_type or 'application/octet-stream',
            folder='documents'
        )

        if not storage_path:
            return api.create_response(
                request,
                {"error": "Failed to upload file to storage"},
                status=500
            )

        # Create document record
        document = Document.objects.create(
            storage_path=storage_path,
            filename=file.name,
            content_type=file.content_type,
            size_bytes=file_size,
            student_id=student_id if student_id else None,
            owner_user_id=owner_user_id if owner_user_id else None,
            uploaded_by=uploaded_by if uploaded_by else None,
            metadata={}
        )

        # Generate download URL
        download_url = storage.get_download_url(storage_path)

        return DocumentUploadResponse(
            id=document.id,
            storage_path=document.storage_path,
            filename=document.filename,
            content_type=document.content_type,
            size_bytes=document.size_bytes,
            uploaded_at=document.uploaded_at,
            download_url=download_url,
            expires_in=3600
        )

    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        return api.create_response(
            request,
            {"error": f"Upload failed: {str(e)}"},
            status=500
        )


@api.get("/api/documents/{document_id}/", response=DocumentResponse, tags=["Documents"])
def get_document(request: HttpRequest, document_id: UUID):
    """Get document details with download URL"""
    document = get_object_or_404(Document, id=document_id)
    return enrich_document(document)


@api.get("/api/documents/student/{student_id}/", response=List[DocumentResponse], tags=["Documents"])
def get_student_documents(request: HttpRequest, student_id: UUID):
    """Get all documents for a student"""
    documents = Document.objects.filter(student_id=student_id)
    return [enrich_document(doc) for doc in documents]


@api.delete("/api/documents/{document_id}/", tags=["Documents"])
def delete_document(request: HttpRequest, document_id: UUID):
    """Delete document from database and MinIO storage"""
    document = get_object_or_404(Document, id=document_id)

    # Delete from MinIO
    if document.storage_path:
        storage = get_storage()
        storage.delete_file(document.storage_path)

    # Delete from database
    document.delete()
    return {"success": True, "message": "Document deleted"}


# ============================================
# EMAIL QUEUE ENDPOINTS
# ============================================

@api.get("/api/email_queue/", response=List[EmailQueueResponse], tags=["Email Queue"])
def list_email_queue(request: HttpRequest):
    """Get all email queue entries"""
    emails = EmailQueue.objects.all()
    return [enrich_email(email) for email in emails]


@api.post("/api/email_queue/", response=EmailQueueResponse, tags=["Email Queue"])
def create_email_queue(request: HttpRequest, payload: EmailQueueCreate):
    """Add email to queue"""
    email = EmailQueue.objects.create(**payload.dict())
    return enrich_email(email)


@api.get("/api/email_queue/{email_id}/", response=EmailQueueResponse, tags=["Email Queue"])
def get_email_queue(request: HttpRequest, email_id: UUID):
    """Get email queue entry by ID"""
    email = get_object_or_404(EmailQueue, id=email_id)
    return enrich_email(email)


@api.get("/api/email_queue/pending/", response=List[EmailQueueResponse], tags=["Email Queue"])
def get_pending_emails(request: HttpRequest):
    """Get all pending emails"""
    emails = EmailQueue.objects.filter(status='pending')
    return [enrich_email(email) for email in emails]


@api.delete("/api/email_queue/{email_id}/", tags=["Email Queue"])
def delete_email_queue(request: HttpRequest, email_id: UUID):
    """Delete email queue entry"""
    email = get_object_or_404(EmailQueue, id=email_id)
    email.delete()
    return {"success": True, "message": "Email queue entry deleted"}
