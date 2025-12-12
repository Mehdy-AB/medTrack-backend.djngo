"""
Django models for auth-service matching PostgreSQL schema.
"""
import uuid
import hashlib
import secrets
from django.db import models
from django.contrib.auth.hashers import make_password, check_password as django_check_password
from django.utils import timezone


class RoleChoices(models.TextChoices):
    """Role enum matching PostgreSQL auth_role type."""
    ADMIN = 'admin', 'Admin'
    STUDENT = 'student', 'Student'
    ENCADRANT = 'encadrant', 'Encadrant'


class User(models.Model):
    """
    User model matching auth.users table.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=255, unique=True, db_index=True)
    password_hash = models.TextField()
    first_name = models.CharField(max_length=120, blank=True, null=True)
    last_name = models.CharField(max_length=120, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    role = models.CharField(
        max_length=20,
        choices=RoleChoices.choices,
        default=RoleChoices.STUDENT
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']

    def __str__(self):
        return self.email

    def set_password(self, raw_password: str) -> None:
        """Hash and set password."""
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        """Verify password against stored hash."""
        return django_check_password(raw_password, self.password_hash)

    def to_public_dict(self) -> dict:
        """Return public user data (no password)."""
        return {
            'id': str(self.id),
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def full_name(self) -> str:
        """Return full name."""
        parts = [self.first_name, self.last_name]
        return ' '.join(p for p in parts if p) or self.email


class Session(models.Model):
    """
    Session model for refresh token management.
    Matches auth.sessions table.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    refresh_token_hash = models.TextField()
    issued_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    client_info = models.JSONField(null=True, blank=True)
    revoked = models.BooleanField(default=False)

    class Meta:
        db_table = 'sessions'
        ordering = ['-issued_at']
        indexes = [
            models.Index(fields=['user'], name='idx_sessions_user'),
        ]

    def __str__(self):
        return f"Session {self.id} for {self.user.email}"

    @property
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return timezone.now() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if session is valid (not revoked and not expired)."""
        return not self.revoked and not self.is_expired

    @staticmethod
    def hash_token(token: str) -> str:
        """Hash refresh token for storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    def verify_token(self, token: str) -> bool:
        """Verify refresh token matches stored hash."""
        return self.refresh_token_hash == self.hash_token(token)


class Permission(models.Model):
    """
    Permission model for RBAC.
    Matches auth.permissions table.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=128, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'permissions'
        ordering = ['code']

    def __str__(self):
        return self.code


class RolePermission(models.Model):
    """
    Role-Permission mapping for RBAC.
    Matches auth.role_permissions table.
    """
    role = models.CharField(max_length=20, choices=RoleChoices.choices)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        db_table = 'role_permissions'
        unique_together = ('role', 'permission')

    def __str__(self):
        return f"{self.role} -> {self.permission.code}"

    @classmethod
    def get_permissions_for_role(cls, role: str) -> list:
        """Get all permission codes for a role."""
        return list(
            cls.objects.filter(role=role)
            .values_list('permission__code', flat=True)
        )


class AuditLog(models.Model):
    """
    Audit log for tracking sensitive actions.
    Matches auth.audit_logs table.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='audit_logs'
    )
    action = models.TextField()
    entity = models.CharField(max_length=128, blank=True, null=True)
    entity_id = models.UUIDField(blank=True, null=True)
    details = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user'], name='idx_audit_logs_user'),
            models.Index(fields=['entity', 'entity_id'], name='idx_audit_logs_entity'),
        ]

    def __str__(self):
        return f"{self.action} by {self.user_id} at {self.created_at}"

    @classmethod
    def log(cls, action: str, user=None, entity: str = None, 
            entity_id=None, details: dict = None):
        """Create an audit log entry."""
        return cls.objects.create(
            user=user,
            action=action,
            entity=entity,
            entity_id=entity_id,
            details=details
        )
