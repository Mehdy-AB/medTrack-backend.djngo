from django.db import models
import uuid

# COMM SERVICE MODELS
# References user_id from AUTH-SERVICE, student_id from PROFILE-SERVICE, offer_id from CORE-SERVICE


class Message(models.Model):
    """Internal messaging between users"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender_id = models.UUIDField(db_index=True)  # Reference to auth.users.id
    receiver_id = models.UUIDField(db_index=True)  # Reference to auth.users.id
    subject = models.CharField(max_length=255, blank=True, null=True)
    body = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'messages'
        indexes = [
            models.Index(fields=['sender_id'], name='idx_messages_sender'),
            models.Index(fields=['receiver_id'], name='idx_messages_receiver'),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Message from {self.sender_id} to {self.receiver_id}"


class Notification(models.Model):
    """Push/email/system notifications"""

    NOTIFICATION_TYPES = [
        ('email', 'Email'),
        ('push', 'Push Notification'),
        ('system', 'System Notification'),
    ]

    NOTIFICATION_STATUS = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(db_index=True)  # Reference to auth.users.id
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    related_object_type = models.CharField(max_length=128, blank=True, null=True)
    related_object_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=NOTIFICATION_STATUS, default='pending')
    attempts = models.IntegerField(default=0)
    last_error = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'notifications'
        indexes = [
            models.Index(fields=['user_id'], name='idx_notifications_user'),
            models.Index(fields=['status'], name='idx_notifications_status'),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.type} notification for {self.user_id}"


class Document(models.Model):
    """Stored files metadata (actual files in MinIO/S3)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner_user_id = models.UUIDField(null=True, blank=True)  # Reference to auth.users.id
    student_id = models.UUIDField(null=True, blank=True)  # Reference to profile.students.id
    offer_id = models.UUIDField(null=True, blank=True)  # Reference to core.offers.id
    storage_path = models.CharField(max_length=2048)  # S3/MinIO key
    filename = models.CharField(max_length=512, blank=True, null=True)
    content_type = models.CharField(max_length=255, blank=True, null=True)
    size_bytes = models.BigIntegerField(null=True, blank=True)
    uploaded_by = models.UUIDField(null=True, blank=True)  # Reference to auth.users.id
    uploaded_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'documents'
        indexes = [
            models.Index(fields=['owner_user_id'], name='idx_documents_owner'),
            models.Index(fields=['student_id'], name='idx_documents_student'),
        ]
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Document: {self.filename}"


class EmailQueue(models.Model):
    """Email queue / task tracking"""

    EMAIL_STATUS = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    to_addresses = models.JSONField()  # Array of email addresses
    subject = models.CharField(max_length=255, blank=True, null=True)
    body = models.TextField(blank=True, null=True)
    headers = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=EMAIL_STATUS, default='pending')
    attempts = models.IntegerField(default=0)
    last_error = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'email_queue'
        indexes = [
            models.Index(fields=['status'], name='idx_emailqueue_status'),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Email to {len(self.to_addresses) if isinstance(self.to_addresses, list) else 0} recipients"
