"""Models for offers app."""
import uuid
from django.db import models
from django.core.exceptions import ValidationError


class Offer(models.Model):
    """Internship offer model."""
    
    STATUS_DRAFT = 'draft'
    STATUS_PUBLISHED = 'published'
    STATUS_CLOSED = 'closed'
    
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_PUBLISHED, 'Published'),
        (STATUS_CLOSED, 'Closed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    service_id = models.UUIDField()
    establishment_id = models.UUIDField(null=True, blank=True)
    created_by = models.UUIDField(null=True, blank=True)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    available_slots = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'core"."offers'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.status})"
    
    def clean(self):
        """Validate offer data."""
        if self.period_start and self.period_end and self.period_start > self.period_end:
            raise ValidationError({'period_end': 'End date must be after start date.'})
        if self.available_slots < 0:
            raise ValidationError({'available_slots': 'Available slots cannot be negative.'})
    
    def get_accepted_count(self):
        """Get count of accepted applications."""
        from applications.models import Application
        return Application.objects.filter(
            offer=self,
            status=Application.STATUS_ACCEPTED
        ).count()
    
    def has_available_slots(self):
        """Check if offer has available slots."""
        return self.get_accepted_count() < self.available_slots
