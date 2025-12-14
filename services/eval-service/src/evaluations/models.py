"""Models for evaluations app - grading and evaluation criteria."""
import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Evaluation(models.Model):
    """Final or intermediate evaluations for students."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student_id = models.UUIDField()
    offer_id = models.UUIDField()
    evaluator_id = models.UUIDField(null=True, blank=True, help_text="Encadrant user ID")
    grade = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        help_text="Final grade (e.g., 0-20 scale)"
    )
    comments = models.TextField(null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    validated = models.BooleanField(default=False, help_text="Whether evaluation is finalized")
    validated_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'evaluations'
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['student_id']),
            models.Index(fields=['offer_id']),
        ]
    
    def __str__(self):
        return f"Evaluation for {self.student_id} - Grade: {self.grade}"


class EvaluationSection(models.Model):
    """Breakdown of evaluation criteria/sections."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evaluation = models.ForeignKey(
        Evaluation, 
        on_delete=models.CASCADE, 
        related_name='sections'
    )
    criterion = models.CharField(max_length=255, help_text="Evaluation criterion name")
    score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        help_text="Score for this criterion"
    )
    comments = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'evaluation_sections'
        indexes = [
            models.Index(fields=['evaluation']),
        ]
    
    def __str__(self):
        return f"{self.criterion}: {self.score}"
