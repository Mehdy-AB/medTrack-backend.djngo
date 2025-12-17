"""
Unit tests for core-service affectations app.
Tests Affectation model.
"""
import uuid
from django.test import TestCase
from offers.models import Offer
from applications.models import Application
from affectations.models import Affectation


class AffectationModelTest(TestCase):
    """Test cases for Affectation model."""
    
    def setUp(self):
        """Set up test offer and application."""
        self.offer = Offer.objects.create(
            title="Test Internship",
            service_id=uuid.uuid4(),
            status=Offer.STATUS_PUBLISHED
        )
        self.student_id = uuid.uuid4()
        self.application = Application.objects.create(
            offer=self.offer,
            student_id=self.student_id,
            status=Application.STATUS_ACCEPTED
        )
    
    def test_affectation_creation(self):
        """Test creating an affectation."""
        affectation = Affectation.objects.create(
            application=self.application,
            student_id=self.student_id,
            offer=self.offer
        )
        
        self.assertEqual(affectation.application, self.application)
        self.assertEqual(affectation.student_id, self.student_id)
        self.assertEqual(affectation.offer, self.offer)
        self.assertIsInstance(affectation.id, uuid.UUID)
        self.assertIsNotNone(affectation.assigned_at)
    
    def test_affectation_one_to_one_application(self):
        """Test that affectation has one-to-one relationship with application."""
        affectation = Affectation.objects.create(
            application=self.application,
            student_id=self.student_id,
            offer=self.offer
        )
        
        # Accessing affectation from application
        self.assertEqual(self.application.affectation, affectation)
    
    def test_affectation_duplicate_application(self):
        """Test that creating affectation with same application raises error."""
        Affectation.objects.create(
            application=self.application,
            student_id=self.student_id,
            offer=self.offer
        )
        
        with self.assertRaises(Exception):  # IntegrityError
            Affectation.objects.create(
                application=self.application,
                student_id=self.student_id,
                offer=self.offer
            )
    
    def test_affectation_with_metadata(self):
        """Test affectation with custom metadata."""
        metadata = {
            "start_date": "2024-01-15",
            "supervisor": "Dr. Smith",
            "location": "Building A, Floor 3"
        }
        affectation = Affectation.objects.create(
            application=self.application,
            student_id=self.student_id,
            offer=self.offer,
            metadata=metadata
        )
        
        self.assertEqual(affectation.metadata["start_date"], "2024-01-15")
        self.assertEqual(affectation.metadata["supervisor"], "Dr. Smith")
    
    def test_affectation_str_representation(self):
        """Test string representation."""
        affectation = Affectation.objects.create(
            application=self.application,
            student_id=self.student_id,
            offer=self.offer
        )
        
        str_repr = str(affectation)
        self.assertIn(str(self.student_id), str_repr)
        self.assertIn(self.offer.title, str_repr)
    
    def test_affectation_related_name_from_offer(self):
        """Test accessing affectations through offer."""
        # Create multiple applications and affectations
        app2 = Application.objects.create(
            offer=self.offer,
            student_id=uuid.uuid4(),
            status=Application.STATUS_ACCEPTED
        )
        
        Affectation.objects.create(
            application=self.application,
            student_id=self.student_id,
            offer=self.offer
        )
        Affectation.objects.create(
            application=app2,
            student_id=app2.student_id,
            offer=self.offer
        )
        
        affectations = self.offer.affectations.all()
        self.assertEqual(affectations.count(), 2)
    
    def test_affectation_cascade_delete_application(self):
        """Test that deleting application deletes affectation."""
        affectation = Affectation.objects.create(
            application=self.application,
            student_id=self.student_id,
            offer=self.offer
        )
        
        application_id = self.application.id
        self.application.delete()
        
        # Affectation should be deleted too
        self.assertFalse(Affectation.objects.filter(id=affectation.id).exists())
    
    def test_affectation_cascade_delete_offer(self):
        """Test that deleting offer deletes affectation."""
        affectation = Affectation.objects.create(
            application=self.application,
            student_id=self.student_id,
            offer=self.offer
        )
        
        offer_id = self.offer.id
        self.offer.delete()
        
        # Affectation should be deleted too
        self.assertFalse(Affectation.objects.filter(id=affectation.id).exists())
    
    def test_affectation_ordering(self):
        """Test that affectations are ordered by assigned_at descending."""
        app2 = Application.objects.create(
            offer=self.offer,
            student_id=uuid.uuid4(),
            status=Application.STATUS_ACCEPTED
        )
        
        aff1 = Affectation.objects.create(
            application=self.application,
            student_id=self.student_id,
            offer=self.offer
        )
        aff2 = Affectation.objects.create(
            application=app2,
            student_id=app2.student_id,
            offer=self.offer
        )
        
        affectations = list(Affectation.objects.all())
        self.assertEqual(affectations[0].id, aff2.id)
        self.assertEqual(affectations[1].id, aff1.id)
