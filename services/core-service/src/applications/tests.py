"""
Unit tests for core-service applications app.
Tests Application model including validation and business logic.
"""
import uuid
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from offers.models import Offer
from applications.models import Application


class ApplicationModelTest(TestCase):
    """Test cases for Application model."""
    
    def setUp(self):
        """Set up test offer."""
        self.offer = Offer.objects.create(
            title="Test Internship",
            service_id=uuid.uuid4(),
            available_slots=3,
            status=Offer.STATUS_PUBLISHED
        )
    
    def test_application_creation(self):
        """Test creating an application."""
        student_id = uuid.uuid4()
        application = Application.objects.create(
            offer=self.offer,
            student_id=student_id,
            notes="I am very interested in this position"
        )
        
        self.assertEqual(application.offer, self.offer)
        self.assertEqual(application.student_id, student_id)
        self.assertEqual(application.status, Application.STATUS_SUBMITTED)
        self.assertIsInstance(application.id, uuid.UUID)
        self.assertIsNotNone(application.submitted_at)
    
    def test_application_default_status(self):
        """Test that default status is 'submitted'."""
        application = Application.objects.create(
            offer=self.offer,
            student_id=uuid.uuid4()
        )
        
        self.assertEqual(application.status, Application.STATUS_SUBMITTED)
    
    def test_application_status_choices(self):
        """Test different status choices."""
        student1 = uuid.uuid4()
        student2 = uuid.uuid4()
        student3 = uuid.uuid4()
        student4 = uuid.uuid4()
        
        submitted = Application.objects.create(
            offer=self.offer, student_id=student1, status=Application.STATUS_SUBMITTED
        )
        accepted = Application.objects.create(
            offer=self.offer, student_id=student2, status=Application.STATUS_ACCEPTED
        )
        rejected = Application.objects.create(
            offer=self.offer, student_id=student3, status=Application.STATUS_REJECTED
        )
        cancelled = Application.objects.create(
            offer=self.offer, student_id=student4, status=Application.STATUS_CANCELLED
        )
        
        self.assertEqual(submitted.status, "submitted")
        self.assertEqual(accepted.status, "accepted")
        self.assertEqual(rejected.status, "rejected")
        self.assertEqual(cancelled.status, "cancelled")
    
    def test_application_with_decision(self):
        """Test application with decision fields."""
        decision_by = uuid.uuid4()
        application = Application.objects.create(
            offer=self.offer,
            student_id=uuid.uuid4(),
            status=Application.STATUS_ACCEPTED,
            decision_by=decision_by
        )
        application.decision_at = timezone.now()
        application.save()
        
        self.assertEqual(application.decision_by, decision_by)
        self.assertIsNotNone(application.decision_at)
    
    def test_application_with_metadata(self):
        """Test application with custom metadata."""
        metadata = {
            "documents": ["cv.pdf", "cover_letter.pdf"],
            "score": 85
        }
        application = Application.objects.create(
            offer=self.offer,
            student_id=uuid.uuid4(),
            metadata=metadata
        )
        
        self.assertEqual(len(application.metadata["documents"]), 2)
        self.assertEqual(application.metadata["score"], 85)
    
    def test_application_str_representation(self):
        """Test string representation."""
        student_id = uuid.uuid4()
        application = Application.objects.create(
            offer=self.offer,
            student_id=student_id
        )
        
        str_repr = str(application)
        self.assertIn(str(student_id), str_repr)
        self.assertIn(self.offer.title, str_repr)
    
    def test_application_related_name(self):
        """Test accessing applications through offer."""
        Application.objects.create(offer=self.offer, student_id=uuid.uuid4())
        Application.objects.create(offer=self.offer, student_id=uuid.uuid4())
        
        applications = self.offer.applications.all()
        self.assertEqual(applications.count(), 2)
    
    def test_application_cascade_delete(self):
        """Test that deleting offer deletes applications."""
        application = Application.objects.create(
            offer=self.offer,
            student_id=uuid.uuid4()
        )
        
        offer_id = self.offer.id
        self.offer.delete()
        
        # Application should be deleted too
        self.assertFalse(Application.objects.filter(id=application.id).exists())
    
    def test_application_ordering(self):
        """Test that applications are ordered by submitted_at descending."""
        app1 = Application.objects.create(offer=self.offer, student_id=uuid.uuid4())
        app2 = Application.objects.create(offer=self.offer, student_id=uuid.uuid4())
        
        applications = list(Application.objects.all())
        self.assertEqual(applications[0].id, app2.id)
        self.assertEqual(applications[1].id, app1.id)
