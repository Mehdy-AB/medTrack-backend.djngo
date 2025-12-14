"""Models for attendance app - daily presence tracking and summaries."""
import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class AttendanceRecord(models.Model):
    """Daily presence record for students."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student_id = models.UUIDField()
    offer_id = models.UUIDField()
    date = models.DateField()
    is_present = models.BooleanField(default=False)
    justified = models.BooleanField(default=False, help_text="Whether absence was justified")
    justification_reason = models.TextField(null=True, blank=True)
    marked_by = models.UUIDField(null=True, blank=True, help_text="Encadrant user ID who marked attendance")
    marked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'attendance_records'
        ordering = ['-date']
        unique_together = [['student_id', 'offer_id', 'date']]
        indexes = [
            models.Index(fields=['student_id']),
            models.Index(fields=['offer_id', 'date']),
        ]
    
    def __str__(self):
        status = "Present" if self.is_present else ("Justified" if self.justified else "Absent")
        return f"{self.student_id} - {self.date} - {status}"


class AttendanceSummary(models.Model):
    """Aggregated presence summary for students (≥80% rule)."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student_id = models.UUIDField()
    offer_id = models.UUIDField()
    total_days = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    present_days = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    # Note: presence_rate is calculated in PostgreSQL as GENERATED column
    # We store it here but it should be read-only from app perspective
    presence_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Automatically calculated: (present_days / total_days) * 100"
    )
    validated = models.BooleanField(default=False, help_text="Has ≥80% presence rate")
    validated_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'attendance_summaries'
        unique_together = [['student_id', 'offer_id']]
        indexes = [
            models.Index(fields=['student_id', 'offer_id']),
        ]
    
    def __str__(self):
        return f"{self.student_id} - {self.offer_id} - {self.presence_rate}%"
    
    def calculate_presence_rate(self):
        """Calculate presence rate."""
        if self.total_days == 0:
            return 0
        return round((self.present_days / self.total_days) * 100, 2)
    
    def check_validation(self):
        """Check if presence rate meets ≥80% requirement."""
        return self.presence_rate >= 80
