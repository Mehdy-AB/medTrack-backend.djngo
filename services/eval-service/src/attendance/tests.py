"""
Unit tests for eval-service attendance app.
Tests AttendanceRecord and AttendanceSummary models.
"""
import uuid
from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from attendance.models import AttendanceRecord, AttendanceSummary


class AttendanceRecordModelTest(TestCase):
    """Test cases for AttendanceRecord model."""
    
    def setUp(self):
        """Set up test data."""
        self.student_id = uuid.uuid4()
        self.offer_id = uuid.uuid4()
        self.encadrant_id = uuid.uuid4()
    
    def test_attendance_record_creation(self):
        """Test creating an attendance record."""
        record = AttendanceRecord.objects.create(
            student_id=self.student_id,
            offer_id=self.offer_id,
            date=date.today(),
            is_present=True,
            marked_by=self.encadrant_id
        )
        
        self.assertEqual(record.student_id, self.student_id)
        self.assertEqual(record.offer_id, self.offer_id)
        self.assertTrue(record.is_present)
        self.assertFalse(record.justified)
        self.assertIsInstance(record.id, uuid.UUID)
    
    def test_attendance_record_absent(self):
        """Test creating an absence record."""
        record = AttendanceRecord.objects.create(
            student_id=self.student_id,
            offer_id=self.offer_id,
            date=date.today(),
            is_present=False
        )
        
        self.assertFalse(record.is_present)
        self.assertFalse(record.justified)
    
    def test_attendance_record_justified_absence(self):
        """Test creating a justified absence."""
        record = AttendanceRecord.objects.create(
            student_id=self.student_id,
            offer_id=self.offer_id,
            date=date.today(),
            is_present=False,
            justified=True,
            justification_reason="Medical appointment"
        )
        
        self.assertFalse(record.is_present)
        self.assertTrue(record.justified)
        self.assertEqual(record.justification_reason, "Medical appointment")
    
    def test_attendance_record_unique_constraint(self):
        """Test that student can only have one record per offer per date."""
        AttendanceRecord.objects.create(
            student_id=self.student_id,
            offer_id=self.offer_id,
            date=date.today(),
            is_present=True
        )
        
        # Try to create duplicate
        with self.assertRaises(Exception):  # IntegrityError
            AttendanceRecord.objects.create(
                student_id=self.student_id,
                offer_id=self.offer_id,
                date=date.today(),
                is_present=False
            )
    
    def test_attendance_record_different_dates_allowed(self):
        """Test that multiple records for different dates are allowed."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        record1 = AttendanceRecord.objects.create(
            student_id=self.student_id,
            offer_id=self.offer_id,
            date=today,
            is_present=True
        )
        record2 = AttendanceRecord.objects.create(
            student_id=self.student_id,
            offer_id=self.offer_id,
            date=yesterday,
            is_present=True
        )
        
        self.assertNotEqual(record1.date, record2.date)
    
    def test_attendance_record_str_representation(self):
        """Test string representation."""
        record = AttendanceRecord.objects.create(
            student_id=self.student_id,
            offer_id=self.offer_id,
            date=date.today(),
            is_present=True
        )
        
        str_repr = str(record)
        self.assertIn(str(self.student_id), str_repr)
        self.assertIn("Present", str_repr)
    
    def test_attendance_record_absent_justified_str(self):
        """Test string representation for justified absence."""
        record = AttendanceRecord.objects.create(
            student_id=self.student_id,
            offer_id=self.offer_id,
            date=date.today(),
            is_present=False,
            justified=True
        )
        
        str_repr = str(record)
        self.assertIn("Justified", str_repr)
    
    def test_attendance_record_ordering(self):
        """Test that records are ordered by date descending."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        record1 = AttendanceRecord.objects.create(
            student_id=self.student_id,
            offer_id=self.offer_id,
            date=yesterday,
            is_present=True
        )
        record2 = AttendanceRecord.objects.create(
            student_id=self.student_id,
            offer_id=self.offer_id,
            date=today,
            is_present=True
        )
        
        records = list(AttendanceRecord.objects.filter(student_id=self.student_id))
        self.assertEqual(records[0].date, today)
        self.assertEqual(records[1].date, yesterday)


class AttendanceSummaryModelTest(TestCase):
    """Test cases for AttendanceSummary model."""
    
    def setUp(self):
        """Set up test data."""
        self.student_id = uuid.uuid4()
        self.offer_id = uuid.uuid4()
    
    def test_attendance_summary_creation(self):
        """Test creating an attendance summary."""
        summary = AttendanceSummary.objects.create(
            student_id=self.student_id,
            offer_id=self.offer_id,
            total_days=30,
            present_days=25
        )
        
        self.assertEqual(summary.student_id, self.student_id)
        self.assertEqual(summary.offer_id, self.offer_id)
        self.assertEqual(summary.total_days, 30)
        self.assertEqual(summary.present_days, 25)
        self.assertIsInstance(summary.id, uuid.UUID)
    
    def test_attendance_summary_unique_constraint(self):
        """Test that only one summary per student per offer."""
        AttendanceSummary.objects.create(
            student_id=self.student_id,
            offer_id=self.offer_id,
            total_days=30,
            present_days=25
        )
        
        # Try to create duplicate
        with self.assertRaises(Exception):  # IntegrityError
            AttendanceSummary.objects.create(
                student_id=self.student_id,
                offer_id=self.offer_id,
                total_days=40,
                present_days=30
            )
    
    def test_attendance_summary_calculate_presence_rate(self):
        """Test calculating presence rate."""
        summary = AttendanceSummary.objects.create(
            student_id=self.student_id,
            offer_id=self.offer_id,
            total_days=50,
            present_days=42
        )
        
        calculated_rate = summary.calculate_presence_rate()
        expected_rate = (42 / 50) * 100  # 84.00%
        
        self.assertEqual(calculated_rate, 84.00)
    
    def test_attendance_summary_calculate_zero_days(self):
        """Test calculating presence rate with zero total days."""
        summary = AttendanceSummary.objects.create(
            student_id=self.student_id,
            offer_id=self.offer_id,
            total_days=0,
            present_days=0
        )
        
        calculated_rate = summary.calculate_presence_rate()
        self.assertEqual(calculated_rate, 0)
    
    def test_attendance_summary_check_validation_passing(self):
        """Test check_validation for passing (≥80%) presence rate."""
        summary = AttendanceSummary.objects.create(
            student_id=self.student_id,
            offer_id=self.offer_id,
            total_days=50,
            present_days=42,
            presence_rate=Decimal("84.00")
        )
        
        self.assertTrue(summary.check_validation())
    
    def test_attendance_summary_check_validation_failing(self):
        """Test check_validation for failing (<80%) presence rate."""
        summary = AttendanceSummary.objects.create(
            student_id=self.student_id,
            offer_id=self.offer_id,
            total_days=50,
            present_days=35,
            presence_rate=Decimal("70.00")
        )
        
        self.assertFalse(summary.check_validation())
    
    def test_attendance_summary_check_validation_exactly_80(self):
        """Test check_validation for exactly 80% (should pass)."""
        summary = AttendanceSummary.objects.create(
            student_id=self.student_id,
            offer_id=self.offer_id,
            total_days=50,
            present_days=40,
            presence_rate=Decimal("80.00")
        )
        
        self.assertTrue(summary.check_validation())
    
    def test_attendance_summary_validated_with_timestamp(self):
        """Test validated summary with timestamp."""
        summary = AttendanceSummary.objects.create(
            student_id=self.student_id,
            offer_id=self.offer_id,
            total_days=60,
            present_days=55,
            presence_rate=Decimal("91.67"),
            validated=True
        )
        summary.validated_at = timezone.now()
        summary.save()
        
        self.assertTrue(summary.validated)
        self.assertIsNotNone(summary.validated_at)
    
    def test_attendance_summary_str_representation(self):
        """Test string representation."""
        summary = AttendanceSummary.objects.create(
            student_id=self.student_id,
            offer_id=self.offer_id,
            total_days=40,
            present_days=35,
            presence_rate=Decimal("87.50")
        )
        
        str_repr = str(summary)
        self.assertIn(str(self.student_id), str_repr)
        self.assertIn("87.50", str_repr)
    
    def test_attendance_summary_negative_days_validation(self):
        """Test that negative days are rejected by validators."""
        summary = AttendanceSummary(
            student_id=self.student_id,
            offer_id=self.offer_id,
            total_days=-10,
            present_days=5
        )
        
        with self.assertRaises(ValidationError):
            summary.full_clean()
