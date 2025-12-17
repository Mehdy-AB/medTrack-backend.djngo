"""
Unit tests for profile-service models.
Tests Establishment, Service, Student, and Encadrant models.
"""
import uuid
from django.test import TestCase
from profiles.models import Establishment, Service, Student, Encadrant


class EstablishmentModelTest(TestCase):
    """Test cases for Establishment model."""
    
    def test_establishment_creation(self):
        """Test creating an establishment."""
        establishment = Establishment.objects.create(
            name="CHU Algiers",
            type="University Hospital",
            address="123 Medical Street",
            city="Algiers",
            phone="+213 21 123456"
        )
        
        self.assertEqual(establishment.name, "CHU Algiers")
        self.assertEqual(establishment.type, "University Hospital")
        self.assertEqual(establishment.city, "Algiers")
        self.assertIsInstance(establishment.id, uuid.UUID)
    
    def test_establishment_with_metadata(self):
        """Test creating establishment with metadata."""
        metadata = {
            "capacity": 500,
            "specialties": ["Cardiology", "Neurology"]
        }
        establishment = Establishment.objects.create(
            name="Test Hospital",
            metadata=metadata
        )
        
        self.assertEqual(establishment.metadata["capacity"], 500)
        self.assertEqual(len(establishment.metadata["specialties"]), 2)
    
    def test_establishment_str_representation(self):
        """Test string representation."""
        establishment = Establishment.objects.create(name="CHU Constantine")
        self.assertEqual(str(establishment), "CHU Constantine")
    
    def test_establishment_default_metadata(self):
        """Test default empty metadata."""
        establishment = Establishment.objects.create(name="Test Hospital")
        self.assertEqual(establishment.metadata, {})


class ServiceModelTest(TestCase):
    """Test cases for Service model."""
    
    def setUp(self):
        """Set up test establishment."""
        self.establishment = Establishment.objects.create(
            name="CHU Algiers",
            city="Algiers"
        )
    
    def test_service_creation(self):
        """Test creating a service."""
        service = Service.objects.create(
            establishment=self.establishment,
            name="Cardiology Department",
            description="Heart and cardiovascular care",
            capacity=20
        )
        
        self.assertEqual(service.name, "Cardiology Department")
        self.assertEqual(service.establishment, self.establishment)
        self.assertEqual(service.capacity, 20)
        self.assertIsInstance(service.id, uuid.UUID)
    
    def test_service_cascade_delete(self):
        """Test that deleting establishment deletes services."""
        service = Service.objects.create(
            establishment=self.establishment,
            name="Emergency"
        )
        
        establishment_id = self.establishment.id
        self.establishment.delete()
        
        # Service should be deleted too
        self.assertFalse(Service.objects.filter(id=service.id).exists())
    
    def test_service_related_name(self):
        """Test accessing services through establishment."""
        Service.objects.create(establishment=self.establishment, name="Cardiology")
        Service.objects.create(establishment=self.establishment, name="Neurology")
        
        services = self.establishment.services.all()
        self.assertEqual(services.count(), 2)
    
    def test_service_str_representation(self):
        """Test string representation."""
        service = Service.objects.create(
            establishment=self.establishment,
            name="Pediatrics"
        )
        expected = f"Pediatrics - {self.establishment.name}"
        self.assertEqual(str(service), expected)
    
    def test_service_with_metadata(self):
        """Test service with custom metadata."""
        metadata = {"head_doctor": "Dr. Smith", "floor": 3}
        service = Service.objects.create(
            establishment=self.establishment,
            name="Surgery",
            metadata=metadata
        )
        
        self.assertEqual(service.metadata["head_doctor"], "Dr. Smith")
        self.assertEqual(service.metadata["floor"], 3)


class StudentModelTest(TestCase):
    """Test cases for Student model."""
    
    def test_student_creation(self):
        """Test creating a student profile."""
        user_id = uuid.uuid4()
        student = Student.objects.create(
            user_id=user_id,
            cin="123456789",
            email="student@example.com",
            phone="+213 555 1234",
            first_name="Ahmed",
            last_name="Benali",
            student_number="STU2024001",
            university="University of Algiers",
            program="Medicine",
            year_level=3
        )
        
        self.assertEqual(student.user_id, user_id)
        self.assertEqual(student.cin, "123456789")
        self.assertEqual(student.first_name, "Ahmed")
        self.assertEqual(student.student_number, "STU2024001")
        self.assertEqual(student.year_level, 3)
        self.assertIsInstance(student.id, uuid.UUID)
    
    def test_student_user_id_unique(self):
        """Test that user_id must be unique."""
        user_id = uuid.uuid4()
        Student.objects.create(user_id=user_id)
        
        with self.assertRaises(Exception):  # IntegrityError
            Student.objects.create(user_id=user_id)
    
    def test_student_cin_unique(self):
        """Test that CIN must be unique."""
        Student.objects.create(user_id=uuid.uuid4(), cin="123456")
        
        with self.assertRaises(Exception):  # IntegrityError
            Student.objects.create(user_id=uuid.uuid4(), cin="123456")
    
    def test_student_number_unique(self):
        """Test that student_number must be unique."""
        Student.objects.create(user_id=uuid.uuid4(), student_number="STU001")
        
        with self.assertRaises(Exception):  # IntegrityError
            Student.objects.create(user_id=uuid.uuid4(), student_number="STU001")
    
    def test_student_with_metadata(self):
        """Test student with custom metadata."""
        metadata = {
            "allergies": ["penicillin"],
            "emergency_contact": "+213 555 9999"
        }
        student = Student.objects.create(
            user_id=uuid.uuid4(),
            first_name="Fatima",
            metadata=metadata
        )
        
        self.assertIn("allergies", student.metadata)
        self.assertEqual(student.metadata["emergency_contact"], "+213 555 9999")
    
    def test_student_str_representation(self):
        """Test string representation."""
        student = Student.objects.create(
            user_id=uuid.uuid4(),
            student_number="STU123"
        )
        self.assertIn("STU123", str(student))


class EncadrantModelTest(TestCase):
    """Test cases for Encadrant model."""
    
    def setUp(self):
        """Set up test establishment and service."""
        self.establishment = Establishment.objects.create(
            name="CHU Algiers"
        )
        self.service = Service.objects.create(
            establishment=self.establishment,
            name="Cardiology"
        )
    
    def test_encadrant_creation(self):
        """Test creating an encadrant profile."""
        user_id = uuid.uuid4()
        encadrant = Encadrant.objects.create(
            user_id=user_id,
            cin="987654321",
            email="doctor@example.com",
            phone="+213 555 5678",
            first_name="Dr. Karim",
            last_name="Mansouri",
            establishment=self.establishment,
            service=self.service,
            position="Head of Department",
            speciality="Cardiology"
        )
        
        self.assertEqual(encadrant.user_id, user_id)
        self.assertEqual(encadrant.cin, "987654321")
        self.assertEqual(encadrant.position, "Head of Department")
        self.assertEqual(encadrant.speciality, "Cardiology")
        self.assertEqual(encadrant.establishment, self.establishment)
        self.assertEqual(encadrant.service, self.service)
        self.assertIsInstance(encadrant.id, uuid.UUID)
    
    def test_encadrant_user_id_unique(self):
        """Test that user_id must be unique."""
        user_id = uuid.uuid4()
        Encadrant.objects.create(user_id=user_id)
        
        with self.assertRaises(Exception):  # IntegrityError
            Encadrant.objects.create(user_id=user_id)
    
    def test_encadrant_cin_unique(self):
        """Test that CIN must be unique."""
        Encadrant.objects.create(user_id=uuid.uuid4(), cin="123456")
        
        with self.assertRaises(Exception):  # IntegrityError
            Encadrant.objects.create(user_id=uuid.uuid4(), cin="123456")
    
    def test_encadrant_without_establishment(self):
        """Test creating encadrant without establishment."""
        encadrant = Encadrant.objects.create(
            user_id=uuid.uuid4(),
            first_name="Dr. Sarah"
        )
        
        self.assertIsNone(encadrant.establishment)
        self.assertIsNone(encadrant.service)
    
    def test_encadrant_establishment_set_null_on_delete(self):
        """Test that deleting establishment sets encadrant.establishment to NULL."""
        encadrant = Encadrant.objects.create(
            user_id=uuid.uuid4(),
            establishment=self.establishment
        )
        
        self.establishment.delete()
        encadrant.refresh_from_db()
        
        self.assertIsNone(encadrant.establishment)
    
    def test_encadrant_with_metadata(self):
        """Test encadrant with custom metadata."""
        metadata = {
            "certifications": ["Board Certified"],
            "languages": ["Arabic", "French", "English"]
        }
        encadrant = Encadrant.objects.create(
            user_id=uuid.uuid4(),
            first_name="Dr. Yasmine",
            metadata=metadata
        )
        
        self.assertEqual(len(encadrant.metadata["languages"]), 3)
        self.assertIn("Board Certified", encadrant.metadata["certifications"])
    
    def test_encadrant_str_representation(self):
        """Test string representation."""
        user_id = uuid.uuid4()
        encadrant = Encadrant.objects.create(
            user_id=user_id,
            position="Surgeon"
        )
        self.assertIn(str(user_id), str(encadrant))
        self.assertIn("Surgeon", str(encadrant))
    
    def test_encadrant_related_names(self):
        """Test accessing encadrants through establishment and service."""
        Encadrant.objects.create(
            user_id=uuid.uuid4(),
            establishment=self.establishment,
            service=self.service
        )
        Encadrant.objects.create(
            user_id=uuid.uuid4(),
            establishment=self.establishment
        )
        
        establishment_encadrants = self.establishment.encadrants.all()
        service_encadrants = self.service.encadrants.all()
        
        self.assertEqual(establishment_encadrants.count(), 2)
        self.assertEqual(service_encadrants.count(), 1)
