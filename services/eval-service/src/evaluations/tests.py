"""
Unit tests for eval-service evaluations app.
Tests Evaluation and EvaluationSection models.
"""
import uuid
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from evaluations.models import Evaluation, EvaluationSection


class EvaluationModelTest(TestCase):
    """Test cases for Evaluation model."""
    
    def test_evaluation_creation(self):
        """Test creating an evaluation."""
        student_id = uuid.uuid4()
        offer_id = uuid.uuid4()
        evaluator_id = uuid.uuid4()
        
        evaluation = Evaluation.objects.create(
            student_id=student_id,
            offer_id=offer_id,
            evaluator_id=evaluator_id,
            grade=Decimal("15.50"),
            comments="Good performance overall"
        )
        
        self.assertEqual(evaluation.student_id, student_id)
        self.assertEqual(evaluation.offer_id, offer_id)
        self.assertEqual(evaluation.evaluator_id, evaluator_id)
        self.assertEqual(evaluation.grade, Decimal("15.50"))
        self.assertFalse(evaluation.validated)
        self.assertIsInstance(evaluation.id, uuid.UUID)
    
    def test_evaluation_without_grade(self):
        """Test creating evaluation without grade (draft)."""
        evaluation = Evaluation.objects.create(
            student_id=uuid.uuid4(),
            offer_id=uuid.uuid4()
        )
        
        self.assertIsNone(evaluation.grade)
        self.assertFalse(evaluation.validated)
    
    def test_evaluation_grade_range_validation(self):
        """Test that grade validators work (0-20 scale)."""
        evaluation = Evaluation(
            student_id=uuid.uuid4(),
            offer_id=uuid.uuid4(),
            grade=Decimal("25.00")  # Over max
        )
        
        with self.assertRaises(ValidationError):
            evaluation.full_clean()
    
    def test_evaluation_negative_grade_validation(self):
        """Test that negative grades are rejected."""
        evaluation = Evaluation(
            student_id=uuid.uuid4(),
            offer_id=uuid.uuid4(),
            grade=Decimal("-5.00")
        )
        
        with self.assertRaises(ValidationError):
            evaluation.full_clean()
    
    def test_evaluation_validation_with_timestamp(self):
        """Test validated evaluation with timestamp."""
        evaluation = Evaluation.objects.create(
            student_id=uuid.uuid4(),
            offer_id=uuid.uuid4(),
            grade=Decimal("16.00"),
            validated=True
        )
        evaluation.validated_at = timezone.now()
        evaluation.save()
        
        self.assertTrue(evaluation.validated)
        self.assertIsNotNone(evaluation.validated_at)
    
    def test_evaluation_with_metadata(self):
        """Test evaluation with custom metadata."""
        metadata = {
            "period": "2024-Q1",
            "type": "midterm",
            "location": "CHU Algiers"
        }
        evaluation = Evaluation.objects.create(
            student_id=uuid.uuid4(),
            offer_id=uuid.uuid4(),
            metadata=metadata
        )
        
        self.assertEqual(evaluation.metadata["type"], "midterm")
        self.assertEqual(evaluation.metadata["location"], "CHU Algiers")
    
    def test_evaluation_str_representation(self):
        """Test string representation."""
        student_id = uuid.uuid4()
        evaluation = Evaluation.objects.create(
            student_id=student_id,
            offer_id=uuid.uuid4(),
            grade=Decimal("14.75")
        )
        
        str_repr = str(evaluation)
        self.assertIn(str(student_id), str_repr)
        self.assertIn("14.75", str_repr)
    
    def test_evaluation_ordering(self):
        """Test that evaluations are ordered by submitted_at descending."""
        eval1 = Evaluation.objects.create(
            student_id=uuid.uuid4(),
            offer_id=uuid.uuid4()
        )
        eval2 = Evaluation.objects.create(
            student_id=uuid.uuid4(),
            offer_id=uuid.uuid4()
        )
        
        evaluations = list(Evaluation.objects.all())
        self.assertEqual(evaluations[0].id, eval2.id)
        self.assertEqual(evaluations[1].id, eval1.id)


class EvaluationSectionModelTest(TestCase):
    """Test cases for EvaluationSection model."""
    
    def setUp(self):
        """Set up test evaluation."""
        self.evaluation = Evaluation.objects.create(
            student_id=uuid.uuid4(),
            offer_id=uuid.uuid4()
        )
    
    def test_evaluation_section_creation(self):
        """Test creating an evaluation section."""
        section = EvaluationSection.objects.create(
            evaluation=self.evaluation,
            criterion="Clinical Skills",
            score=Decimal("17.00"),
            comments="Excellent bedside manner"
        )
        
        self.assertEqual(section.evaluation, self.evaluation)
        self.assertEqual(section.criterion, "Clinical Skills")
        self.assertEqual(section.score, Decimal("17.00"))
        self.assertEqual(section.comments, "Excellent bedside manner")
        self.assertIsInstance(section.id, uuid.UUID)
    
    def test_evaluation_section_without_score(self):
        """Test creating section without score."""
        section = EvaluationSection.objects.create(
            evaluation=self.evaluation,
            criterion="Communication"
        )
        
        self.assertIsNone(section.score)
    
    def test_evaluation_section_score_validation(self):
        """Test that score validators work (0-20 scale)."""
        section = EvaluationSection(
            evaluation=self.evaluation,
            criterion="Test",
            score=Decimal("30.00")  # Over max
        )
        
        with self.assertRaises(ValidationError):
            section.full_clean()
    
    def test_evaluation_section_related_name(self):
        """Test accessing sections through evaluation."""
        EvaluationSection.objects.create(
            evaluation=self.evaluation,
            criterion="Clinical Skills",
            score=Decimal("16.00")
        )
        EvaluationSection.objects.create(
            evaluation=self.evaluation,
            criterion="Theoretical Knowledge",
            score=Decimal("18.00")
        )
        
        sections = self.evaluation.sections.all()
        self.assertEqual(sections.count(), 2)
    
    def test_evaluation_section_cascade_delete(self):
        """Test that deleting evaluation deletes sections."""
        section = EvaluationSection.objects.create(
            evaluation=self.evaluation,
            criterion="Test Criterion"
        )
        
        evaluation_id = self.evaluation.id
        self.evaluation.delete()
        
        # Section should be deleted too
        self.assertFalse(EvaluationSection.objects.filter(id=section.id).exists())
    
    def test_evaluation_section_str_representation(self):
        """Test string representation."""
        section = EvaluationSection.objects.create(
            evaluation=self.evaluation,
            criterion="Professionalism",
            score=Decimal("19.50")
        )
        
        expected = "Professionalism: 19.50"
        self.assertEqual(str(section), expected)
    
    def test_evaluation_multiple_sections(self):
        """Test evaluation with multiple detailed sections."""
        criteria = [
            ("Clinical Skills", Decimal("17.00")),
            ("Theoretical Knowledge", Decimal("18.50")),
            ("Communication", Decimal("16.00")),
            ("Professionalism", Decimal("19.00")),
            ("Technical Skills", Decimal("15.50"))
        ]
        
        for criterion, score in criteria:
            EvaluationSection.objects.create(
                evaluation=self.evaluation,
                criterion=criterion,
                score=score
            )
        
        sections = self.evaluation.sections.all()
        self.assertEqual(sections.count(), 5)
        
        # Calculate average
        total = sum(s.score for s in sections if s.score)
        average = total / sections.count()
        self.assertAlmostEqual(float(average), 17.20, places=2)
