"""
Unit tests for core-service offers app.
Tests Offer model including validation and business logic.
"""
import uuid
from datetime import date, timedelta
from django.test import TestCase
from django.core.exceptions import ValidationError
from offers.models import Offer


class OfferModelTest(TestCase):
    """Test cases for Offer model."""
    
    def test_offer_creation(self):
        """Test creating a basic offer."""
        service_id = uuid.uuid4()
        offer = Offer.objects.create(
            title="Cardiology Internship",
            description="6-month internship in cardiology department",
            service_id=service_id,
            period_start=date.today(),
            period_end=date.today() + timedelta(days=180),
            available_slots=5,
            status=Offer.STATUS_PUBLISHED
        )
        
        self.assertEqual(offer.title, "Cardiology Internship")
        self.assertEqual(offer.service_id, service_id)
        self.assertEqual(offer.available_slots, 5)
        self.assertEqual(offer.status, Offer.STATUS_PUBLISHED)
        self.assertIsInstance(offer.id, uuid.UUID)
    
    def test_offer_default_status(self):
        """Test that default status is 'draft'."""
        offer = Offer.objects.create(
            title="Test Offer",
            service_id=uuid.uuid4()
        )
        
        self.assertEqual(offer.status, Offer.STATUS_DRAFT)
    
    def test_offer_default_slots(self):
        """Test that default available_slots is 1."""
        offer = Offer.objects.create(
            title="Test Offer",
            service_id=uuid.uuid4()
        )
        
        self.assertEqual(offer.available_slots, 1)
    
    def test_offer_status_choices(self):
        """Test different status choices."""
        service_id = uuid.uuid4()
        
        draft = Offer.objects.create(title="Draft", service_id=service_id, status=Offer.STATUS_DRAFT)
        published = Offer.objects.create(title="Published", service_id=service_id, status=Offer.STATUS_PUBLISHED)
        closed = Offer.objects.create(title="Closed", service_id=service_id, status=Offer.STATUS_CLOSED)
        
        self.assertEqual(draft.status, "draft")
        self.assertEqual(published.status, "published")
        self.assertEqual(closed.status, "closed")
    
    def test_offer_period_validation(self):
        """Test that period_end must be after period_start."""
        offer = Offer(
            title="Test Offer",
            service_id=uuid.uuid4(),
            period_start=date.today(),
            period_end=date.today() - timedelta(days=1)  # End before start
        )
        
        with self.assertRaises(ValidationError) as context:
            offer.clean()
        
        self.assertIn('period_end', context.exception.message_dict)
    
    def test_offer_negative_slots_validation(self):
        """Test that available_slots cannot be negative."""
        offer = Offer(
            title="Test Offer",
            service_id=uuid.uuid4(),
            available_slots=-1
        )
        
        with self.assertRaises(ValidationError) as context:
            offer.clean()
        
        self.assertIn('available_slots', context.exception.message_dict)
    
    def test_offer_with_metadata(self):
        """Test offer with custom metadata."""
        metadata = {
            "requirements": ["Medical License", "Clean Record"],
            "benefits": ["Stipend", "Accommodation"]
        }
        offer = Offer.objects.create(
            title="Premium Internship",
            service_id=uuid.uuid4(),
            metadata=metadata
        )
        
        self.assertEqual(len(offer.metadata["requirements"]), 2)
        self.assertIn("Stipend", offer.metadata["benefits"])
    
    def test_offer_str_representation(self):
        """Test string representation."""
        offer = Offer.objects.create(
            title="Surgery Internship",
            service_id=uuid.uuid4(),
            status=Offer.STATUS_PUBLISHED
        )
        
        expected = "Surgery Internship (published)"
        self.assertEqual(str(offer), expected)
    
    def test_offer_with_creator(self):
        """Test offer with created_by field."""
        creator_id = uuid.uuid4()
        offer = Offer.objects.create(
            title="Test Offer",
            service_id=uuid.uuid4(),
            created_by=creator_id
        )
        
        self.assertEqual(offer.created_by, creator_id)
    
    def test_offer_with_establishment(self):
        """Test offer with establishment_id."""
        establishment_id = uuid.uuid4()
        offer = Offer.objects.create(
            title="Test Offer",
            service_id=uuid.uuid4(),
            establishment_id=establishment_id
        )
        
        self.assertEqual(offer.establishment_id, establishment_id)
    
    def test_offer_ordering(self):
        """Test that offers are ordered by created_at descending."""
        offer1 = Offer.objects.create(title="First", service_id=uuid.uuid4())
        offer2 = Offer.objects.create(title="Second", service_id=uuid.uuid4())
        
        offers = list(Offer.objects.all())
        self.assertEqual(offers[0].title, "Second")
        self.assertEqual(offers[1].title, "First")
