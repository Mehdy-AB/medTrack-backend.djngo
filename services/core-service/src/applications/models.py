"""Models for applications app."""
import uuid
from django.db import models
from django.core.exceptions import ValidationError
from offers.models import Offer


class Application(models.Model):
    """Student application to an offer."""
    
    STATUS_SUBMITTED = 'submitted'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name='applications')
    student_id = models.UUIDField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SUBMITTED)
    decision_at = models.DateTimeField(null=True, blank=True)
    decision_by = models.UUIDField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'core"."applications'
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['offer', 'student_id']),
            models.Index(fields=['student_id']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Application {self.id} - Student {self.student_id} for {self.offer.title}"
    
    def clean(self):
        """Validate application."""
        # Check for existing active application (not rejected or cancelled)
        if not self.pk:  # Only on creation
            active_statuses = [self.STATUS_SUBMITTED, self.STATUS_ACCEPTED]
            existing = Application.objects.filter(
                offer=self.offer,
                student_id=self.student_id,
                status__in=active_statuses
            ).exists()
            if existing:
                raise ValidationError(
                    'An active application for this offer already exists.'
                )
