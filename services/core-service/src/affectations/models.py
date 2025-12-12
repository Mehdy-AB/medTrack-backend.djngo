"""Models for affectations app."""
import uuid
from django.db import models
from applications.models import Application
from offers.models import Offer


class Affectation(models.Model):
    """Assignment of a student to an offer."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='affectation')
    student_id = models.UUIDField()
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name='affectations')
    assigned_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'core"."affectations'
        ordering = ['-assigned_at']
        indexes = [
            models.Index(fields=['student_id']),
            models.Index(fields=['offer']),
        ]
    
    def __str__(self):
        return f"Affectation {self.id} - Student {self.student_id} to {self.offer.title}"
