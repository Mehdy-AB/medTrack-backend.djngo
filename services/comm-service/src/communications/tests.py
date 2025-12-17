"""
Unit tests for comm-service communications app.
Tests Message, Notification, Document, and EmailQueue models.
"""
import uuid
from django.test import TestCase
from django.utils import timezone
from communications.models import Message, Notification, Document, EmailQueue


class MessageModelTest(TestCase):
    """Test cases for Message model."""
    
    def setUp(self):
        """Set up test data."""
        self.sender_id = uuid.uuid4()
        self.receiver_id = uuid.uuid4()
    
    def test_message_creation(self):
        """Test creating a message."""
        message = Message.objects.create(
            sender_id=self.sender_id,
            receiver_id=self.receiver_id,
            subject="Internship Question",
            body="When does the internship start?"
        )
        
        self.assertEqual(message.sender_id, self.sender_id)
        self.assertEqual(message.receiver_id, self.receiver_id)
        self.assertEqual(message.subject, "Internship Question")
        self.assertIsNone(message.read_at)
        self.assertIsInstance(message.id, uuid.UUID)
    
    def test_message_read_status(self):
        """Test marking message as read."""
        message = Message.objects.create(
            sender_id=self.sender_id,
            receiver_id=self.receiver_id,
            subject="Test",
            body="Test message"
        )
        
        # Mark as read
        message.read_at = timezone.now()
        message.save()
        
        self.assertIsNotNone(message.read_at)
    
    def test_message_with_metadata(self):
        """Test message with custom metadata."""
        metadata = {
            "priority": "high",
            "category": "urgent",
            "attachments": ["file1.pdf"]
        }
        message = Message.objects.create(
            sender_id=self.sender_id,
            receiver_id=self.receiver_id,
            body="Important message",
            metadata=metadata
        )
        
        self.assertEqual(message.metadata["priority"], "high")
        self.assertEqual(len(message.metadata["attachments"]), 1)
    
    def test_message_str_representation(self):
        """Test string representation."""
        message = Message.objects.create(
            sender_id=self.sender_id,
            receiver_id=self.receiver_id,
            subject="Test Subject"
        )
        
        str_repr = str(message)
        self.assertIn(str(self.sender_id), str_repr)
        self.assertIn(str(self.receiver_id), str_repr)
    
    def test_message_ordering(self):
        """Test that messages are ordered by created_at descending."""
        msg1 = Message.objects.create(
            sender_id=self.sender_id,
            receiver_id=self.receiver_id,
            subject="First"
        )
        msg2 = Message.objects.create(
            sender_id=self.sender_id,
            receiver_id=self.receiver_id,
            subject="Second"
        )
        
        messages = list(Message.objects.all())
        self.assertEqual(messages[0].subject, "Second")
        self.assertEqual(messages[1].subject, "First")


class NotificationModelTest(TestCase):
    """Test cases for Notification model."""
    
    def setUp(self):
        """Set up test data."""
        self.user_id = uuid.uuid4()
    
    def test_notification_creation(self):
        """Test creating a notification."""
        notification = Notification.objects.create(
            user_id=self.user_id,
            type="email",
            title="New Application",
            content="You have a new application to review"
        )
        
        self.assertEqual(notification.user_id, self.user_id)
        self.assertEqual(notification.type, "email")
        self.assertEqual(notification.status, "pending")
        self.assertEqual(notification.attempts, 0)
        self.assertIsInstance(notification.id, uuid.UUID)
    
    def test_notification_types(self):
        """Test different notification types."""
        email_notif = Notification.objects.create(
            user_id=self.user_id,
            type="email",
            content="Email notification"
        )
        push_notif = Notification.objects.create(
            user_id=self.user_id,
            type="push",
            content="Push notification"
        )
        system_notif = Notification.objects.create(
            user_id=self.user_id,
            type="system",
            content="System notification"
        )
        
        self.assertEqual(email_notif.type, "email")
        self.assertEqual(push_notif.type, "push")
        self.assertEqual(system_notif.type, "system")
    
    def test_notification_status_progression(self):
        """Test notification status changes."""
        notification = Notification.objects.create(
            user_id=self.user_id,
            type="email",
            content="Test notification"
        )
        
        # Initially pending
        self.assertEqual(notification.status, "pending")
        
        # Mark as sent
        notification.status = "sent"
        notification.sent_at = timezone.now()
        notification.attempts = 1
        notification.save()
        
        self.assertEqual(notification.status, "sent")
        self.assertIsNotNone(notification.sent_at)
        self.assertEqual(notification.attempts, 1)
    
    def test_notification_failed_status(self):
        """Test notification failure tracking."""
        notification = Notification.objects.create(
            user_id=self.user_id,
            type="email",
            content="Test"
        )
        
        notification.status = "failed"
        notification.attempts = 3
        notification.last_error = "SMTP connection timeout"
        notification.save()
        
        self.assertEqual(notification.status, "failed")
        self.assertEqual(notification.attempts, 3)
        self.assertIsNotNone(notification.last_error)
    
    def test_notification_with_related_object(self):
        """Test notification linked to related object."""
        offer_id = uuid.uuid4()
        notification = Notification.objects.create(
            user_id=self.user_id,
            type="system",
            content="New offer available",
            related_object_type="Offer",
            related_object_id=offer_id
        )
        
        self.assertEqual(notification.related_object_type, "Offer")
        self.assertEqual(notification.related_object_id, offer_id)
    
    def test_notification_with_metadata(self):
        """Test notification with custom metadata."""
        metadata = {
            "action_url": "/offers/123",
            "icon": "bell",
            "sound": "default"
        }
        notification = Notification.objects.create(
            user_id=self.user_id,
            type="push",
            content="Test",
            metadata=metadata
        )
        
        self.assertEqual(notification.metadata["action_url"], "/offers/123")
    
    def test_notification_str_representation(self):
        """Test string representation."""
        notification = Notification.objects.create(
            user_id=self.user_id,
            type="email",
            content="Test"
        )
        
        str_repr = str(notification)
        self.assertIn("email", str_repr)
        self.assertIn(str(self.user_id), str_repr)


class DocumentModelTest(TestCase):
    """Test cases for Document model."""
    
    def test_document_creation(self):
        """Test creating a document."""
        owner_id = uuid.uuid4()
        document = Document.objects.create(
            owner_user_id=owner_id,
            storage_path="uploads/2024/document123.pdf",
            filename="CV_JohnDoe.pdf",
            content_type="application/pdf",
            size_bytes=125000,
            uploaded_by=owner_id
        )
        
        self.assertEqual(document.owner_user_id, owner_id)
        self.assertEqual(document.filename, "CV_JohnDoe.pdf")
        self.assertEqual(document.content_type, "application/pdf")
        self.assertEqual(document.size_bytes, 125000)
        self.assertIsInstance(document.id, uuid.UUID)
    
    def test_document_linked_to_student(self):
        """Test document linked to a student."""
        student_id = uuid.uuid4()
        document = Document.objects.create(
            student_id=student_id,
            storage_path="students/docs/transcript.pdf",
            filename="transcript.pdf"
        )
        
        self.assertEqual(document.student_id, student_id)
    
    def test_document_linked_to_offer(self):
        """Test document linked to an offer."""
        offer_id = uuid.uuid4()
        document = Document.objects.create(
            offer_id=offer_id,
            storage_path="offers/docs/description.pdf",
            filename="offer_description.pdf"
        )
        
        self.assertEqual(document.offer_id, offer_id)
    
    def test_document_with_metadata(self):
        """Test document with custom metadata."""
        metadata = {
            "thumbnail_url": "/thumbnails/doc123.jpg",
            "checksum": "abc123def456",
            "version": 2
        }
        document = Document.objects.create(
            storage_path="path/to/file.pdf",
            filename="file.pdf",
            metadata=metadata
        )
        
        self.assertEqual(document.metadata["version"], 2)
        self.assertIn("checksum", document.metadata)
    
    def test_document_str_representation(self):
        """Test string representation."""
        document = Document.objects.create(
            storage_path="path/to/file.pdf",
            filename="MyDocument.pdf"
        )
        
        self.assertIn("MyDocument.pdf", str(document))
    
    def test_document_ordering(self):
        """Test that documents are ordered by uploaded_at descending."""
        doc1 = Document.objects.create(
            storage_path="path1.pdf",
            filename="first.pdf"
        )
        doc2 = Document.objects.create(
            storage_path="path2.pdf",
            filename="second.pdf"
        )
        
        documents = list(Document.objects.all())
        self.assertEqual(documents[0].filename, "second.pdf")
        self.assertEqual(documents[1].filename, "first.pdf")


class EmailQueueModelTest(TestCase):
    """Test cases for EmailQueue model."""
    
    def test_email_queue_creation(self):
        """Test creating an email queue entry."""
        email = EmailQueue.objects.create(
            to_addresses=["user1@example.com", "user2@example.com"],
            subject="Welcome to MedTrack",
            body="Your account has been created."
        )
        
        self.assertEqual(len(email.to_addresses), 2)
        self.assertEqual(email.subject, "Welcome to MedTrack")
        self.assertEqual(email.status, "pending")
        self.assertEqual(email.attempts, 0)
        self.assertIsInstance(email.id, uuid.UUID)
    
    def test_email_queue_single_recipient(self):
        """Test email with single recipient."""
        email = EmailQueue.objects.create(
            to_addresses=["student@example.com"],
            subject="Test",
            body="Test email"
        )
        
        self.assertEqual(len(email.to_addresses), 1)
        self.assertEqual(email.to_addresses[0], "student@example.com")
    
    def test_email_queue_status_sent(self):
        """Test email marked as sent."""
        email = EmailQueue.objects.create(
            to_addresses=["test@example.com"],
            subject="Test",
            body="Body"
        )
        
        email.status = "sent"
        email.sent_at = timezone.now()
        email.attempts = 1
        email.save()
        
        self.assertEqual(email.status, "sent")
        self.assertIsNotNone(email.sent_at)
    
    def test_email_queue_status_failed(self):
        """Test email marked as failed."""
        email = EmailQueue.objects.create(
            to_addresses=["test@example.com"],
            subject="Test",
            body="Body"
        )
        
        email.status = "failed"
        email.attempts = 5
        email.last_error = "SMTP server unreachable"
        email.save()
        
        self.assertEqual(email.status, "failed")
        self.assertEqual(email.attempts, 5)
        self.assertEqual(email.last_error, "SMTP server unreachable")
    
    def test_email_queue_with_headers(self):
        """Test email with custom headers."""
        headers = {
            "X-Priority": "1",
            "X-Mailer": "MedTrack",
            "Reply-To": "noreply@medtrack.com"
        }
        email = EmailQueue.objects.create(
            to_addresses=["test@example.com"],
            subject="Test",
            body="Body",
            headers=headers
        )
        
        self.assertEqual(email.headers["X-Priority"], "1")
        self.assertEqual(email.headers["Reply-To"], "noreply@medtrack.com")
    
    def test_email_queue_scheduled(self):
        """Test scheduled email."""
        future_time = timezone.now() + timezone.timedelta(hours=24)
        email = EmailQueue.objects.create(
            to_addresses=["test@example.com"],
            subject="Scheduled Email",
            body="This will be sent tomorrow",
            scheduled_at=future_time
        )
        
        self.assertIsNotNone(email.scheduled_at)
        self.assertGreater(email.scheduled_at, timezone.now())
    
    def test_email_queue_str_representation(self):
        """Test string representation."""
        email = EmailQueue.objects.create(
            to_addresses=["user1@example.com", "user2@example.com", "user3@example.com"],
            subject="Test",
            body="Body"
        )
        
        str_repr = str(email)
        self.assertIn("3", str_repr)  # Number of recipients
    
    def test_email_queue_ordering(self):
        """Test that emails are ordered by created_at descending."""
        email1 = EmailQueue.objects.create(
            to_addresses=["test1@example.com"],
            subject="First"
        )
        email2 = EmailQueue.objects.create(
            to_addresses=["test2@example.com"],
            subject="Second"
        )
        
        emails = list(EmailQueue.objects.all())
        self.assertEqual(emails[0].subject, "Second")
        self.assertEqual(emails[1].subject, "First")
