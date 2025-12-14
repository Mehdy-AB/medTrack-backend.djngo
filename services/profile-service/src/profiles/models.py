from django.db import models
import uuid

# PROFILE SERVICE MODELS
# References user_id from AUTH-SERVICE (no FK constraint since it's in another database)

class Establishment(models.Model):
    """Hospitals/Medical establishments"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=120, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'establishments'
        indexes = [
            models.Index(fields=['city'], name='idx_establishments_city'),
        ]

    def __str__(self):
        return self.name


class Service(models.Model):
    """Departments/Units inside hospitals"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    establishment = models.ForeignKey(
        Establishment,
        on_delete=models.CASCADE,
        related_name='services'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    capacity = models.IntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'services'
        indexes = [
            models.Index(fields=['establishment'], name='idx_services_establishment'),
        ]

    def __str__(self):
        return f"{self.name} - {self.establishment.name}"


class Student(models.Model):
    """Student profiles - references user_id from auth-service"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(unique=True, db_index=True)  # Reference to auth.users.id (no FK)
    cin = models.CharField(max_length=64, unique=True, blank=True, null=True)  # National ID
    email = models.EmailField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    student_number = models.CharField(max_length=64, unique=True, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    university = models.CharField(max_length=255, blank=True, null=True)
    program = models.CharField(max_length=255, blank=True, null=True)
    year_level = models.IntegerField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)  # Changed from 'extra' to 'metadata' for consistency
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'students'
        indexes = [
            models.Index(fields=['user_id'], name='idx_students_user'),
        ]

    def __str__(self):
        return f"Student {self.student_number or self.user_id}"


class Encadrant(models.Model):
    """Supervisor/Mentor profiles - references user_id from auth-service"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(unique=True, db_index=True)  # Reference to auth.users.id (no FK)
    cin = models.CharField(max_length=64, unique=True, blank=True, null=True)  # National ID
    email = models.EmailField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    establishment = models.ForeignKey(
        Establishment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='encadrants'
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='encadrants'
    )
    position = models.CharField(max_length=255, blank=True, null=True)
    speciality = models.CharField(max_length=255, blank=True, null=True)  # Changed from 'specialty' for consistency
    metadata = models.JSONField(default=dict, blank=True)  # Changed from 'contact' to 'metadata'
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'encadrants'
        indexes = [
            models.Index(fields=['user_id'], name='idx_encadrants_user'),
            models.Index(fields=['establishment'], name='idx_encadrants_establishment'),
        ]

    def __str__(self):
        return f"Encadrant {self.user_id} - {self.position or 'N/A'}"