# Profile Service API & Events Documentation

## Overview
The **Profile Service** manages user profiles (Students, Encadrants), Establishments (Hospitals), and Services (Hospital Departments). It automatically creates profiles when users register in the AUTH-SERVICE through event-driven architecture.

## Base URL
`http://localhost/profile/api`

---

## Event-Driven Architecture

### How Profile Service Works

```
AUTH-SERVICE creates user
    ↓
    Publishes event → RabbitMQ (events.topic exchange)
    ↓ Routing Key: auth.user.created
    ↓
PROFILE-SERVICE receives event# COMM SERVICE - Complete Implementation Guide

## 📋 Overview
The Communication Service handles messages, notifications, and file uploads using modern technologies. It listens to events from other services and sends notifications accordingly.

---

## 🏗️ Architecture Components

### Technology Stack
- **Django 5.0+** with Django REST Framework
- **PostgreSQL 15+** for database
- **RabbitMQ** for event-driven messaging
- **Consul** for service discovery
- **Celery** for background task processing
- **Redis** for Celery broker and caching
- **Firebase Cloud Messaging (FCM)** for push notifications
- **Mailgun/SendGrid** for email delivery
- **MinIO/S3** for file storage
- **WebSockets (Django Channels)** for real-time messaging

---

## 📁 Project Structure

```
comm-service/
├── manage.py
├── requirements.txt
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py              # For WebSockets
│   └── celery.py            # Celery configuration
├── core/
│   ├── __init__.py
│   ├── consul_client.py
│   ├── rabbitmq_client.py
│   └── event_consumer.py
├── communications/
│   ├── __init__.py
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── consumers.py         # WebSocket consumers
│   ├── tasks.py             # Celery tasks
│   ├── events.py            # Event handlers
│   └── services/
│       ├── __init__.py
│       ├── notification_service.py
│       ├── email_service.py
│       ├── push_service.py
│       └── storage_service.py
└── docker-compose.yml
```

---

## 🔧 Step 1: Dependencies

### requirements.txt
```txt
Django==5.0.0
djangorestframework==3.14.0
psycopg2-binary==2.9.9
python-consul==1.1.0
pika==1.3.2
celery==5.3.4
redis==5.0.1
django-redis==5.4.0
channels==4.0.0
channels-redis==4.1.0
daphne==4.0.0
boto3==1.34.0              # For S3/MinIO
firebase-admin==6.3.0      # For FCM push notifications
sendgrid==6.11.0           # For email (alternative: mailgun)
Pillow==10.1.0
python-magic==0.4.27
requests==2.31.0
```

---

## 🗄️ Step 2: Database Models

### communications/models.py
```python
import uuid
from django.db import models
from django.utils import timezone

class Message(models.Model):
    """Internal messaging between users"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender_id = models.UUIDField(db_index=True)
    receiver_id = models.UUIDField(db_index=True)
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'comm_messages'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sender_id']),
            models.Index(fields=['receiver_id']),
            models.Index(fields=['created_at']),
        ]

    def mark_as_read(self):
        if not self.read_at:
            self.read_at = timezone.now()
            self.save(update_fields=['read_at'])


class NotificationType(models.TextChoices):
    EMAIL = 'email', 'Email'
    PUSH = 'push', 'Push Notification'
    SYSTEM = 'system', 'System Notification'
    SMS = 'sms', 'SMS'


class NotificationStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    SENT = 'sent', 'Sent'
    FAILED = 'failed', 'Failed'
    SCHEDULED = 'scheduled', 'Scheduled'


class Notification(models.Model):
    """Notifications for users"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(db_index=True)
    type = models.CharField(max_length=20, choices=NotificationType.choices)
    title = models.CharField(max_length=255)
    content = models.TextField()
    
    # Related object references
    related_object_type = models.CharField(max_length=128, blank=True)
    related_object_id = models.UUIDField(null=True, blank=True)
    
    # Delivery tracking
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=NotificationStatus.choices,
        default=NotificationStatus.PENDING
    )
    attempts = models.IntegerField(default=0)
    last_error = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'comm_notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def mark_as_read(self):
        if not self.read_at:
            self.read_at = timezone.now()
            self.save(update_fields=['read_at'])


class Document(models.Model):
    """File metadata for uploaded documents"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Ownership
    owner_user_id = models.UUIDField(null=True, blank=True, db_index=True)
    student_id = models.UUIDField(null=True, blank=True, db_index=True)
    offer_id = models.UUIDField(null=True, blank=True, db_index=True)
    
    # File details
    storage_path = models.CharField(max_length=2048)  # S3/MinIO key
    filename = models.CharField(max_length=512)
    content_type = models.CharField(max_length=255)
    size_bytes = models.BigIntegerField()
    
    # Upload tracking
    uploaded_by = models.UUIDField(db_index=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # File status
    is_public = models.BooleanField(default=False)
    virus_scanned = models.BooleanField(default=False)
    scan_result = models.CharField(max_length=50, blank=True)
    
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'comm_documents'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['owner_user_id']),
            models.Index(fields=['student_id']),
            models.Index(fields=['uploaded_by']),
        ]


class EmailQueue(models.Model):
    """Email queue for async sending"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    to_addresses = models.JSONField()  # Array of email addresses
    subject = models.CharField(max_length=255)
    body = models.TextField()
    html_body = models.TextField(blank=True)
    headers = models.JSONField(default=dict, blank=True)
    
    # Scheduling
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=NotificationStatus.choices,
        default=NotificationStatus.PENDING
    )
    attempts = models.IntegerField(default=0)
    last_error = models.TextField(blank=True)

    class Meta:
        db_table = 'comm_email_queue'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['scheduled_at']),
        ]


class DeviceToken(models.Model):
    """FCM device tokens for push notifications"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(db_index=True)
    device_token = models.CharField(max_length=512, unique=True)
    platform = models.CharField(max_length=20)  # 'android', 'ios', 'web'
    device_info = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'comm_device_tokens'
        indexes = [
            models.Index(fields=['user_id', 'is_active']),
        ]
```

---

## 🔥 Step 3: Firebase Push Notification Service

### communications/services/push_service.py
```python
import logging
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
from ..models import DeviceToken

logger = logging.getLogger(__name__)

class PushNotificationService:
    """Firebase Cloud Messaging push notification service"""
    
    def __init__(self):
        if not firebase_admin._apps:
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
    
    def send_to_user(self, user_id, title, body, data=None):
        """Send push notification to all user's devices"""
        try:
            tokens = DeviceToken.objects.filter(
                user_id=user_id,
                is_active=True
            ).values_list('device_token', flat=True)
            
            if not tokens:
                logger.warning(f"No active device tokens for user {user_id}")
                return
            
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                tokens=list(tokens)
            )
            
            response = messaging.send_multicast(message)
            logger.info(f"✅ Sent push notification to {response.success_count} devices")
            
            # Handle failed tokens
            if response.failure_count > 0:
                failed_tokens = [
                    tokens[idx] for idx, resp in enumerate(response.responses)
                    if not resp.success
                ]
                self._deactivate_tokens(failed_tokens)
            
            return response
        
        except Exception as e:
            logger.error(f"❌ Failed to send push notification: {e}", exc_info=True)
            raise
    
    def _deactivate_tokens(self, tokens):
        """Deactivate invalid tokens"""
        DeviceToken.objects.filter(device_token__in=tokens).update(is_active=False)
        logger.info(f"Deactivated {len(tokens)} invalid device tokens")

push_service = PushNotificationService()
```

---

## 📧 Step 4: Email Service

### communications/services/email_service.py
```python
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from django.conf import settings

logger = logging.getLogger(__name__)

class EmailService:
    """SendGrid email service"""
    
    def __init__(self):
        self.client = SendGridAPIClient(settings.SENDGRID_API_KEY)
        self.from_email = settings.DEFAULT_FROM_EMAIL
    
    def send_email(self, to_addresses, subject, body, html_body=None):
        """Send email via SendGrid"""
        try:
            message = Mail(
                from_email=Email(self.from_email),
                to_emails=[To(email) for email in to_addresses],
                subject=subject,
                plain_text_content=Content("text/plain", body)
            )
            
            if html_body:
                message.add_content(Content("text/html", html_body))
            
            response = self.client.send(message)
            logger.info(f"✅ Email sent successfully: {response.status_code}")
            return response.status_code == 202
        
        except Exception as e:
            logger.error(f"❌ Failed to send email: {e}", exc_info=True)
            return False
    
    def send_welcome_email(self, email, first_name):
        """Send welcome email to new user"""
        subject = "Welcome to Internship Management System"
        body = f"""
        Hello {first_name},
        
        Welcome to our Internship Management System! We're excited to have you on board.
        
        You can now:
        - Browse available internship offers
        - Submit applications
        - Track your progress
        - Communicate with supervisors
        
        Best regards,
        The Team
        """
        
        html_body = f"""
        <html>
        <body>
            <h2>Welcome to Internship Management System</h2>
            <p>Hello {first_name},</p>
            <p>Welcome to our Internship Management System! We're excited to have you on board.</p>
            <h3>You can now:</h3>
            <ul>
                <li>Browse available internship offers</li>
                <li>Submit applications</li>
                <li>Track your progress</li>
                <li>Communicate with supervisors</li>
            </ul>
            <p>Best regards,<br>The Team</p>
        </body>
        </html>
        """
        
        return self.send_email([email], subject, body, html_body)

email_service = EmailService()
```

---

## 💾 Step 5: File Storage Service

### communications/services/storage_service.py
```python
import logging
import boto3
from django.conf import settings
import mimetypes
import hashlib

logger = logging.getLogger(__name__)

class StorageService:
    """MinIO/S3 file storage service"""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.MINIO_ENDPOINT,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            region_name=settings.MINIO_REGION
        )
        self.bucket_name = settings.MINIO_BUCKET
    
    def upload_file(self, file_obj, folder='documents'):
        """Upload file to MinIO/S3"""
        try:
            # Generate unique filename
            file_hash = hashlib.md5(file_obj.read()).hexdigest()
            file_obj.seek(0)
            
            filename = file_obj.name
            storage_path = f"{folder}/{file_hash}/{filename}"
            
            # Upload file
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                storage_path,
                ExtraArgs={
                    'ContentType': file_obj.content_type or mimetypes.guess_type(filename)[0]
                }
            )
            
            logger.info(f"✅ File uploaded: {storage_path}")
            return storage_path
        
        except Exception as e:
            logger.error(f"❌ Failed to upload file: {e}", exc_info=True)
            raise
    
    def get_presigned_url(self, storage_path, expiration=3600):
        """Generate presigned URL for file download"""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': storage_path
                },
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            logger.error(f"❌ Failed to generate presigned URL: {e}")
            raise
    
    def delete_file(self, storage_path):
        """Delete file from storage"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=storage_path
            )
            logger.info(f"✅ File deleted: {storage_path}")
        except Exception as e:
            logger.error(f"❌ Failed to delete file: {e}")
            raise

storage_service = StorageService()
```

---

## 📬 Step 6: Notification Service

### communications/services/notification_service.py
```python
import logging
from ..models import Notification, NotificationType, NotificationStatus
from .push_service import push_service
from .email_service import email_service
from ..tasks import send_notification_async

logger = logging.getLogger(__name__)

class NotificationService:
    """Central notification service"""
    
    def send_notification(self, user_id, title, content, 
                         notification_type=NotificationType.SYSTEM,
                         related_object_type=None, related_object_id=None,
                         send_async=True):
        """
        Create and send a notification
        
        Args:
            user_id: UUID of the user
            title: Notification title
            content: Notification content
            notification_type: Type of notification (email, push, system)
            related_object_type: Type of related object (e.g., 'offer', 'application')
            related_object_id: UUID of related object
            send_async: Whether to send asynchronously via Celery
        """
        try:
            # Create notification record
            notification = Notification.objects.create(
                user_id=user_id,
                type=notification_type,
                title=title,
                content=content,
                related_object_type=related_object_type or '',
                related_object_id=related_object_id,
                status=NotificationStatus.PENDING
            )
            
            logger.info(f"📝 Created notification {notification.id} for user {user_id}")
            
            # Send notification
            if send_async:
                send_notification_async.delay(str(notification.id))
            else:
                self._send_notification(notification)
            
            return notification
        
        except Exception as e:
            logger.error(f"❌ Failed to create notification: {e}", exc_info=True)
            raise
    
    def _send_notification(self, notification):
        """Actually send the notification"""
        try:
            if notification.type == NotificationType.PUSH:
                push_service.send_to_user(
                    notification.user_id,
                    notification.title,
                    notification.content,
                    data={'notification_id': str(notification.id)}
                )
            
            elif notification.type == NotificationType.EMAIL:
                # Get user email from Consul (AUTH-SERVICE)
                user_email = self._get_user_email(notification.user_id)
                if user_email:
                    email_service.send_email(
                        [user_email],
                        notification.title,
                        notification.content
                    )
            
            # Mark as sent
            notification.status = NotificationStatus.SENT
            notification.sent_at = timezone.now()
            notification.save()
            
            logger.info(f"✅ Sent notification {notification.id}")
        
        except Exception as e:
            notification.status = NotificationStatus.FAILED
            notification.last_error = str(e)
            notification.attempts += 1
            notification.save()
            logger.error(f"❌ Failed to send notification {notification.id}: {e}")
            raise
    
    def _get_user_email(self, user_id):
        """Get user email from AUTH-SERVICE via Consul"""
        from core.consul_client import consul_client
        import requests
        
        auth_url = consul_client.get_service_url('auth-service')
        if auth_url:
            response = requests.get(f"{auth_url}/api/users/{user_id}/")
            if response.status_code == 200:
                return response.json().get('email')
        return None

notification_service = NotificationService()
```

---

## ⚡ Step 7: Celery Tasks

### communications/tasks.py
```python
from celery import shared_task
import logging
from .models import Notification, EmailQueue, NotificationStatus
from .services.notification_service import notification_service
from .services.email_service import email_service

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_notification_async(self, notification_id):
    """Async task to send notification"""
    try:
        notification = Notification.objects.get(id=notification_id)
        notification_service._send_notification(notification)
    except Notification.DoesNotExist:
        logger.error(f"Notification {notification_id} not found")
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

@shared_task
def process_email_queue():
    """Process pending emails in queue"""
    pending_emails = EmailQueue.objects.filter(
        status=NotificationStatus.PENDING
    )[:100]
    
    for email in pending_emails:
        try:
            success = email_service.send_email(
                email.to_addresses,
                email.subject,
                email.body,
                email.html_body
            )
            
            if success:
                email.status = NotificationStatus.SENT
                email.sent_at = timezone.now()
            else:
                email.status = NotificationStatus.FAILED
                email.attempts += 1
            
            email.save()
        
        except Exception as e:
            logger.error(f"Failed to send email {email.id}: {e}")
            email.status = NotificationStatus.FAILED
            email.last_error = str(e)
            email.attempts += 1
            email.save()
```

---

## 🎯 Step 8: Event Handlers

### communications/events.py
```python
import logging
from .services.notification_service import notification_service
from .services.email_service import email_service
from .models import NotificationType

logger = logging.getLogger(__name__)

class CommunicationEventHandler:
    """Handle events from other services"""
    
    @staticmethod
    def handle_profile_created(event_data):
        """
        Handle PROFILE_CREATED event
        Send welcome notification to new user
        
        Expected event:
        {
            "event_type": "PROFILE_CREATED",
            "user_id": "uuid",
            "role": "student|encadrant",
            "profile_id": "uuid",
            "_meta": {...}
        }
        """
        try:
            user_id = event_data.get('user_id')
            role = event_data.get('role')
            
            logger.info(f"📥 Processing PROFILE_CREATED event for user_id={user_id}, role={role}")
            
            # Send welcome notification
            if role == 'student':
                notification_service.send_notification(
                    user_id=user_id,
                    title="Welcome to Internship Management System!",
                    content="Your student profile has been created. Start exploring internship offers now!",
                    notification_type=NotificationType.SYSTEM
                )
                
                # Also send push notification if user has device token
                notification_service.send_notification(
                    user_id=user_id,
                    title="Welcome!",
                    content="Your account is ready. Start your internship journey!",
                    notification_type=NotificationType.PUSH
                )
            
            elif role == 'encadrant':
                notification_service.send_notification(
                    user_id=user_id,
                    title="Welcome to Internship Management System!",
                    content="Your supervisor profile has been created. You can now manage internship offers.",
                    notification_type=NotificationType.SYSTEM
                )
            
            logger.info(f"✅ Sent welcome notifications to user_id={user_id}")
        
        except Exception as e:
            logger.error(f"❌ Error handling PROFILE_CREATED event: {e}", exc_info=True)
    
    @staticmethod
    def handle_application_submitted(event_data):
        """
        Handle APPLICATION_SUBMITTED event
        Notify encadrant about new application
        """
        try:
            student_id = event_data.get('student_id')
            encadrant_id = event_data.get('encadrant_id')
            offer_title = event_data.get('offer_title', 'an internship')
            
            logger.info(f"📥 Processing APPLICATION_SUBMITTED event")
            
            # Notify encadrant
            notification_service.send_notification(
                user_id=encadrant_id,
                title="New Internship Application",
                content=f"You have received a new application for {offer_title}",
                notification_type=NotificationType.SYSTEM,
                related_object_type='application',
                related_object_id=event_data.get('application_id')
            )
            
            # Also send push
            notification_service.send_notification(
                user_id=encadrant_id,
                title="New Application",
                content=f"New application for {offer_title}",
                notification_type=NotificationType.PUSH
            )
            
            logger.info(f"✅ Sent application notification to encadrant {encadrant_id}")
        
        except Exception as e:
            logger.error(f"❌ Error handling APPLICATION_SUBMITTED event: {e}")
    
    @staticmethod
    def handle_application_accepted(event_data):
        """Handle APPLICATION_ACCEPTED event"""
        try:
            student_id = event_data.get('student_id')
            offer_title = event_data.get('offer_title', 'internship')
            
            # Notify student
            notification_service.send_notification(
                user_id=student_id,
                title="Application Accepted! 🎉",
                content=f"Congratulations! Your application for {offer_title} has been accepted.",
                notification_type=NotificationType.SYSTEM
            )
            
            notification_service.send_notification(
                user_id=student_id,
                title="Application Accepted!",
                content=f"Your application for {offer_title} was accepted!",
                notification_type=NotificationType.PUSH
            )
            
            logger.info(f"✅ Sent acceptance notification to student {student_id}")
        
        except Exception as e:
            logger.error(f"❌ Error handling APPLICATION_ACCEPTED event: {e}")
```

---

## 🎧 Step 9: Event Consumer Setup

### core/event_consumer.py (COMM-SERVICE)
```python
import logging
import json
from core.rabbitmq_client import rabbitmq_client
from communications.events import CommunicationEventHandler

logger = logging.getLogger(__name__)

class CommEventConsumer:
    """Event consumer for COMM-SERVICE"""
    
    def setup(self):
        """Setup RabbitMQ exchanges, queues, and bindings"""
        logger.info("⚙️ Setting up COMM-SERVICE event listener...")
        
        rabbitmq_client.connect()
        rabbitmq_client.declare_exchange('events', 'topic')
        rabbitmq_client.declare_queue('comm_service_events')
        
        # Bind to multiple event patterns
        bindings = [
            'profile.*.created',        # Profile creation events
            'application.submitted',    # Application events
            'application.accepted',
            'application.rejected',
            'offer.published',          # Offer events
        ]
        
        for routing_key in bindings:
            rabbitmq_client.bind_queue(
                queue_name='comm_service_events',
                exchange_name='events',
                routing_key=routing_key
            )
        
        logger.info("✅ COMM-SERVICE event setup complete")
    
    def callback(self, ch, method, properties, body):
        """Process incoming events"""
        try:
            event_data = json.loads(body)
            event_type = event_data.get('event_type')
            
            logger.info(f"📨 Received event: {event_type}")
            
            # Route to handlers
            if event_type == 'PROFILE_CREATED':
                CommunicationEventHandler.handle_profile_created(event_data)
            elif event_type == 'APPLICATION_SUBMITTED':
                CommunicationEventHandler.handle_application_submitted(event_data)
            elif event_type == 'APPLICATION_ACCEPTED':
                CommunicationEventHandler.handle_application_accepted(event_data)
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
        
        except Exception as e:
            logger.error(f"❌ Error processing event: {e}", exc_info=True)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def start(self):
        """Start consuming"""
        self.setup()
        rabbitmq_client.consume('comm_service_events', self.callback)
```

---

## 🔧 Step 10: Celery Configuration

### config/celery.py
```python
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('comm_service')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Periodic tasks
app.conf.beat_schedule = {
    'process-email-queue': {
        'task': 'communications.tasks.process_email_queue',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
}
```

---

## 📱 Step 11: WebSocket Support (Real-time Messaging)

### communications/consumers.py
```python
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message

class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time messaging"""
    
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_group_name = f'chat_{self.user_id}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'chat_message':
            await self.save_message(data)
            await self.channel_layer.group_send(
                f"chat_{data['receiver_id']}",
                {
                    'type': 'chat_message',
                    'message': data
                }
            )
    
    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event['message']))
    
    @database_sync_to_async
    def save_message(self, data):
        Message.objects.create(
            sender_id=data['sender_id'],
            receiver_id=data['receiver_id'],
            body=data['body']
        )
```

### communications/routing.py
```python
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<user_id>[0-9a-f-]+)/$', consumers.ChatConsumer.as_asgi()),
]
```

### config/asgi.py
```python
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from communications.routing import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
```

---

## 🐳 Step 12: Docker Compose

### docker-compose.yml
```yaml
version: '3.8'

services:
  comm-service:
    build: .
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/comm_db
      - REDIS_URL=redis://redis:6379/0
      - RABBITMQ_HOST=rabbitmq
      - CONSUL_HOST=consul
      - SENDGRID_API_KEY=your_key
      - MINIO_ENDPOINT=http://minio:9000
    ports:
      - "8003:8003"
    depends_on:
      - postgres
      - redis
      - rabbitmq
      - consul
      - minio
    command: daphne -b 0.0.0.0 -p 8003 config.asgi:application

  celery-worker:
    build: .
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/comm_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
      - postgres
    command: celery -A config worker -l info

  celery-beat:
    build: .
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
    command: celery -A config beat -l info

  event-consumer:
    build: .
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/comm_db
      - RABBITMQ_HOST=rabbitmq
    depends_on:
      - rabbitmq
      - postgres
    command: python manage.py consume_events

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  minio:
    image: minio/minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    command: server /data --console-address ":9001"
```

---

## ✅ Key Benefits Summary

### 🔥 Modern Technology Stack
- **Firebase FCM**: Cross-platform push notifications
- **SendGrid**: Reliable email delivery with analytics
- **WebSockets**: Real-time messaging
- **Celery**: Async task processing
- **Redis**: Fast caching and message broker
- **MinIO/S3**: Scalable file storage

### 🎯 Event-Driven Notifications
- **Automatic triggers**: Welcome emails, application updates
- **Multi-channel**: System, push, email, SMS
- **Retry mechanism**: Failed notifications are retried
- **Tracking**: Full audit trail of all notifications

### 🚀 Scalability
- **Async processing**: Non-blocking notification sending
- **Queue-based**: Handle high notification volumes
- **Real-time**: WebSocket support for instant messages
- **Distributed**: Multiple workers for parallel processing

---

## 📝 Usage Examples

### Send Welcome Notification
```python
from communications.services.notification_service import notification_service

notification_service.send_notification(
    user_id=user_id,
    title="Welcome!",
    content="Your account is ready.",
    notification_type=NotificationType.PUSH
)
```

### Upload File
```python
from communications.services.storage_service import storage_service

storage_path = storage_service.upload_file(file_obj, folder='documents')
url = storage_service.get_presigned_url(storage_path)
```

This comprehensive guide provides a modern, scalable communication service! 🚀
    ↓
    Creates Student or Encadrant profile automatically
    ↓
    Publishes event → RabbitMQ
    ↓ Routing Key: profile.student.created or profile.encadrant.created
    ↓
COMM-SERVICE or other services can consume this event
```

### Events Consumed by PROFILE-SERVICE

Profile Service listens to these events from **AUTH-SERVICE**:

#### 1. User Created Event
**Routing Key:** `auth.user.created`
**Exchange:** `events.topic`

When AUTH-SERVICE creates a new user, PROFILE-SERVICE automatically creates the appropriate profile.

**Event Structure:**
```json
{
  "event_type": "USER_CREATED",
  "user_id": "a1b2c3d4-...",
  "email": "student@example.com",
  "role": "student",
  "first_name": "John",
  "last_name": "Doe",
  "_meta": {
    "timestamp": "2025-12-13T10:00:00Z",
    "routing_key": "auth.user.created",
    "source": "auth-service"
  }
}
```

**What Happens:**
- If `role = "student"` → Creates a Student profile
- If `role = "encadrant"` → Creates an Encadrant profile
- If `role = "admin"` → No profile created (admins don't need profiles)

---

### Events Published by PROFILE-SERVICE

#### 1. Student Profile Created
**Routing Key:** `student.created`
**Published When:** A new student profile is created

```json
{
  "event_type": "STUDENT_CREATED",
  "payload": {
    "student_id": "uuid",
    "user_id": "uuid",
    "cin": "AB123456",
    "email": "student@example.com",
    "phone": "+1234567890",
    "first_name": "John",
    "last_name": "Doe",
    "created_at": "2025-12-13T10:00:00Z"
  },
  "service": "profile-service",
  "timestamp": "2025-12-13T10:00:00Z",
  "version": "1.0"
}
```

#### 2. Encadrant Profile Created
**Routing Key:** `encadrant.created`
**Published When:** A new encadrant profile is created

```json
{
  "event_type": "ENCADRANT_CREATED",
  "payload": {
    "encadrant_id": "uuid",
    "user_id": "uuid",
    "cin": "CD789012",
    "email": "encadrant@example.com",
    "phone": "+0987654321",
    "first_name": "Dr. Jane",
    "last_name": "Smith",
    "created_at": "2025-12-13T10:00:00Z"
  },
  "service": "profile-service",
  "timestamp": "2025-12-13T10:00:00Z",
  "version": "1.0"
}
```

#### 3. Other Events
- `student.updated` - When a student profile is updated
- `student.deleted` - When a student profile is deleted
- `encadrant.updated` - When an encadrant profile is updated
- `encadrant.deleted` - When an encadrant profile is deleted
- `establishment.created` - When a new establishment is created
- `service.created` - When a new hospital service/department is created

---

## API Endpoints

### Student Endpoints

#### 1. List All Students
**GET** `/students/`

**Response (200 OK):**
```json
[
  {
    "id": "student-uuid",
    "user_id": "user-uuid",
    "cin": "AB123456",
    "email": "student@example.com",
    "phone": "+1234567890",
    "first_name": "John",
    "last_name": "Doe",
    "student_number": "STU2025001",
    "date_of_birth": "2000-01-15",
    "university": "Mohammed V University",
    "program": "Medicine",
    "year_level": 3,
    "metadata": {},
    "user_data": { ... },
    "created_at": "2025-12-13T10:00:00Z",
    "updated_at": "2025-12-13T10:00:00Z"
  }
]
```

#### 2. Get Student by ID
**GET** `/students/{id}/`

**Response (200 OK):**
```json
{
  "id": "student-uuid",
  "user_id": "user-uuid",
  "cin": "AB123456",
  "email": "student@example.com",
  "phone": "+1234567890",
  "first_name": "John",
  "last_name": "Doe",
  "student_number": "STU2025001",
  "date_of_birth": "2000-01-15",
  "university": "Mohammed V University",
  "program": "Medicine",
  "year_level": 3,
  "metadata": {},
  "user_data": {
    "id": "user-uuid",
    "email": "student@example.com",
    "role": "student",
    "is_active": true
  },
  "created_at": "2025-12-13T10:00:00Z",
  "updated_at": "2025-12-13T10:00:00Z"
}
```

#### 3. Get Student by User ID
**GET** `/students/by_user/{user_id}/`

Returns the student profile for a given user_id (includes user data from AUTH-SERVICE via Consul).

#### 4. Create Student Profile (Manual)
**POST** `/students/`

**Request:**
```json
{
  "user_id": "user-uuid",
  "cin": "AB123456",
  "email": "student@example.com",
  "phone": "+1234567890",
  "first_name": "John",
  "last_name": "Doe",
  "student_number": "STU2025001",
  "date_of_birth": "2000-01-15",
  "university": "Mohammed V University",
  "program": "Medicine",
  "year_level": 3
}
```

**Response (201 Created):**
Returns created student object + publishes `student.created` event.

#### 5. Update Student Profile
**PUT/PATCH** `/students/{id}/`

**Request:**
```json
{
  "phone": "+1112223333",
  "university": "Hassan II University",
  "year_level": 4
}
```

**Response (200 OK):**
Returns updated student object + publishes `student.updated` event.

#### 6. Delete Student Profile
**DELETE** `/students/{id}/`

**Response (204 No Content)**
Publishes `student.deleted` event.

---

### Encadrant Endpoints

#### 1. List All Encadrants
**GET** `/encadrants/`

#### 2. Get Encadrant by ID
**GET** `/encadrants/{id}/`

#### 3. Get Encadrant by User ID
**GET** `/encadrants/by_user/{user_id}/`

#### 4. Get Encadrants by Establishment
**GET** `/encadrants/by_establishment/{establishment_id}/`

Returns all encadrants working in a specific establishment.

#### 5. Create Encadrant Profile
**POST** `/encadrants/`

**Request:**
```json
{
  "user_id": "user-uuid",
  "cin": "CD789012",
  "email": "encadrant@example.com",
  "phone": "+0987654321",
  "first_name": "Dr. Jane",
  "last_name": "Smith",
  "establishment": "establishment-uuid",
  "service": "service-uuid",
  "position": "Senior Consultant",
  "speciality": "Cardiology"
}
```

**Response (201 Created):**
Returns created encadrant object + publishes `encadrant.created` event.

#### 6. Update/Delete Encadrant
**PUT/PATCH/DELETE** `/encadrants/{id}/`

Similar to Student endpoints.

---

### Establishment Endpoints

#### 1. List All Establishments
**GET** `/establishments/`

#### 2. Get Establishment by ID
**GET** `/establishments/{id}/`

#### 3. Get Establishments by City
**GET** `/establishments/by_city/{city}/`

Example: `/establishments/by_city/Casablanca/`

#### 4. Create Establishment
**POST** `/establishments/`

**Request:**
```json
{
  "name": "Hospital Central",
  "type": "Public Hospital",
  "address": "123 Main Street",
  "city": "Casablanca",
  "phone": "+212-5-XXXX-XXXX",
  "metadata": {
    "capacity": 500,
    "specialties": ["Cardiology", "Neurology", "Surgery"]
  }
}
```

**Response (201 Created):**
Publishes `establishment.created` event.

---

### Service (Department) Endpoints

#### 1. List All Services
**GET** `/services/`

#### 2. Get Service by ID
**GET** `/services/{id}/`

#### 3. Get Services by Establishment
**GET** `/services/by_establishment/{establishment_id}/`

Returns all services/departments within a specific hospital.

#### 4. Create Service
**POST** `/services/`

**Request:**
```json
{
  "establishment": "establishment-uuid",
  "name": "Cardiology Department",
  "description": "Specialized in heart conditions",
  "capacity": 50,
  "metadata": {
    "head_doctor": "Dr. Smith",
    "equipment": ["ECG", "Ultrasound"]
  }
}
```

---

### My Profile Endpoint

#### Get Current User's Profile
**GET** `/me`

**Headers:** `X-User-ID: {user_id}`

This endpoint:
1. Gets user_id from X-User-ID header
2. Calls AUTH-SERVICE (via Consul) to get user role
3. Returns student or encadrant profile based on role

**Response for Student:**
```json
{
  "id": "student-uuid",
  "user_id": "user-uuid",
  "cin": "AB123456",
  "email": "student@example.com",
  ...
}
```

**Response for Encadrant:**
```json
{
  "id": "encadrant-uuid",
  "user_id": "user-uuid",
  "cin": "CD789012",
  "email": "encadrant@example.com",
  ...
}
```

---

## Service Discovery with Consul

Profile Service uses **Consul** to discover other microservices:

### How It Works

1. When PROFILE-SERVICE needs to call AUTH-SERVICE:
   ```python
   # Instead of hardcoded URL
   auth_url = "http://auth-service:8000"  # ❌ Old way

   # Uses Consul for discovery
   auth_url = consul.get_service_url('auth-service')  # ✅ New way
   # Returns: http://auth-service:8000 (discovered dynamically)
   ```

2. Benefits:
   - No hardcoded URLs
   - Automatic failover if a service goes down
   - Load balancing across multiple instances
   - Health checks ensure only healthy services are used

### Registering Profile Service with Consul

Profile Service automatically registers itself on startup:

```python
# In register_service.py
consul.register(
    name='profile-service',
    address='profile-service',
    port=8002,
    health_check='http://profile-service:8002/health/'
)
```

---

## Testing the Event Flow

### Test 1: User Registration Creates Profile

1. **Register a new student in AUTH-SERVICE:**
   ```bash
   curl -X POST http://localhost/auth/api/v1/register \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test.student@example.com",
       "password": "SecurePass123!",
       "first_name": "Test",
       "last_name": "Student",
       "phone": "+1234567890",
       "role": "student"
     }'
   ```

2. **AUTH-SERVICE publishes `auth.user.created` event to RabbitMQ**

3. **PROFILE-SERVICE automatically creates Student profile**

4. **Verify profile was created:**
   ```bash
   # Get the user_id from registration response
   curl http://localhost/profile/api/students/by_user/{user_id}/
   ```

5. **PROFILE-SERVICE publishes `student.created` event**

6. **COMM-SERVICE (or other services) can consume this event to send welcome email**

---

## Database Models

### Student
```python
- id: UUID (Primary Key)
- user_id: UUID (Unique, references AUTH-SERVICE user)
- cin: String (National ID)
- email: Email
- phone: String
- first_name: String
- last_name: String
- student_number: String (Unique)
- date_of_birth: Date
- university: String
- program: String
- year_level: Integer
- metadata: JSON (flexible extra data)
- created_at: DateTime
- updated_at: DateTime
```

### Encadrant
```python
- id: UUID (Primary Key)
- user_id: UUID (Unique, references AUTH-SERVICE user)
- cin: String (National ID)
- email: Email
- phone: String
- first_name: String
- last_name: String
- establishment: ForeignKey (Establishment)
- service: ForeignKey (Service)
- position: String
- speciality: String
- metadata: JSON
- created_at: DateTime
- updated_at: DateTime
```

### Establishment
```python
- id: UUID (Primary Key)
- name: String
- type: String (e.g., "Public Hospital", "Private Clinic")
- address: Text
- city: String
- phone: String
- metadata: JSON
- created_at: DateTime
- updated_at: DateTime
```

### Service (Hospital Department)
```python
- id: UUID (Primary Key)
- establishment: ForeignKey (Establishment)
- name: String
- description: Text
- capacity: Integer
- metadata: JSON
- created_at: DateTime
- updated_at: DateTime
```

---

## Running the Event Consumer

To start listening for events from AUTH-SERVICE:

```bash
# In profile-service container
python manage.py consume_events
```

Output:
```
================================================================================
🚀 PROFILE-SERVICE Event Consumer
================================================================================
📡 Connecting to RabbitMQ at rabbitmq:5672
📥 Declaring queue: profile.events
🔗 Binding to routing keys: auth.user.created, auth.user.deleted, auth.user.updated

📌 Automatic Profile Creation:
   • auth.user.created (role=student) → creates Student profile
   • auth.user.created (role=encadrant) → creates Encadrant profile

✅ Consumer ready!
📨 Waiting for events... (Press CTRL+C to stop)
```

---

## For Your Friends (Other Service Developers)

### How to Consume PROFILE-SERVICE Events

If you're building COMM-SERVICE, CORE-SERVICE, or any other service and want to react when profiles are created:

```python
# In your service's event consumer

from profiles.events import get_rabbitmq_client

def handle_student_created(event):
    """Called when a new student profile is created"""
    payload = event['payload']
    student_id = payload['student_id']
    email = payload['email']

    # Send welcome email
    send_email(
        to=email,
        subject="Welcome to MedTrack!",
        body=f"Your student profile has been created (ID: {student_id})"
    )

# Setup consumer
rabbitmq = get_rabbitmq_client('rabbitmq', 5672, 'admin', 'password')
rabbitmq.declare_queue('comm.events', ['student.created', 'encadrant.created'])
rabbitmq.consume_events('comm.events', handle_student_created)
```

---

## Summary

- **PROFILE-SERVICE** automatically creates profiles when users register
- Uses **RabbitMQ** for event-driven communication
- Uses **Consul** for service discovery
- Publishes events that other services can consume
- Provides REST APIs for manual profile management
- All profile creation is automatic through events from AUTH-SERVICE
