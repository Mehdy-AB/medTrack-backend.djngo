"""
Unit tests for auth-service models.
Tests User, Session, Permission, RolePermission, and AuditLog models.
"""
import uuid
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from users.models import (
    User, Session, Permission, RolePermission, 
    AuditLog, RoleChoices
)


class UserModelTest(TestCase):
    """Test cases for User model."""
    
    def test_user_creation(self):
        """Test creating a basic user."""
        user = User.objects.create(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            role=RoleChoices.STUDENT
        )
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Doe")
        self.assertEqual(user.role, RoleChoices.STUDENT)
        self.assertTrue(user.is_active)
        self.assertIsInstance(user.id, uuid.UUID)
    
    def test_user_email_unique(self):
        """Test that email must be unique."""
        User.objects.create(email="test@example.com")
        with self.assertRaises(Exception):  # IntegrityError
            User.objects.create(email="test@example.com")
    
    def test_user_password_hashing(self):
        """Test password hashing and verification."""
        user = User.objects.create(email="test@example.com")
        user.set_password("SecurePassword123")
        user.save()
        
        self.assertTrue(user.check_password("SecurePassword123"))
        self.assertFalse(user.check_password("WrongPassword"))
        self.assertNotEqual(user.password_hash, "SecurePassword123")
    
    def test_user_full_name_property(self):
        """Test full_name property."""
        user = User.objects.create(
            email="test@example.com",
            first_name="John",
            last_name="Doe"
        )
        self.assertEqual(user.full_name, "John Doe")
        
        # Test with only first name
        user2 = User.objects.create(
            email="test2@example.com",
            first_name="Jane"
        )
        self.assertEqual(user2.full_name, "Jane")
        
        # Test with no names (should return email)
        user3 = User.objects.create(email="test3@example.com")
        self.assertEqual(user3.full_name, "test3@example.com")
    
    def test_user_to_public_dict(self):
        """Test to_public_dict method."""
        user = User.objects.create(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            role=RoleChoices.ADMIN
        )
        public_data = user.to_public_dict()
        
        self.assertEqual(public_data['email'], "test@example.com")
        self.assertEqual(public_data['first_name'], "John")
        self.assertEqual(public_data['role'], RoleChoices.ADMIN)
        self.assertNotIn('password_hash', public_data)
    
    def test_user_role_choices(self):
        """Test different role choices."""
        admin = User.objects.create(email="admin@example.com", role=RoleChoices.ADMIN)
        student = User.objects.create(email="student@example.com", role=RoleChoices.STUDENT)
        encadrant = User.objects.create(email="encadrant@example.com", role=RoleChoices.ENCADRANT)
        
        self.assertEqual(admin.role, "admin")
        self.assertEqual(student.role, "student")
        self.assertEqual(encadrant.role, "encadrant")


class SessionModelTest(TestCase):
    """Test cases for Session model."""
    
    def setUp(self):
        """Set up test user."""
        self.user = User.objects.create(email="test@example.com")
    
    def test_session_creation(self):
        """Test creating a session."""
        expires_at = timezone.now() + timedelta(days=7)
        session = Session.objects.create(
            user=self.user,
            refresh_token_hash=Session.hash_token("test_token"),
            expires_at=expires_at
        )
        
        self.assertEqual(session.user, self.user)
        self.assertFalse(session.revoked)
        self.assertIsInstance(session.id, uuid.UUID)
    
    def test_session_token_hashing(self):
        """Test token hashing."""
        token = "my_refresh_token_123"
        hash1 = Session.hash_token(token)
        hash2 = Session.hash_token(token)
        
        self.assertEqual(hash1, hash2)
        self.assertNotEqual(hash1, token)
    
    def test_session_token_verification(self):
        """Test verifying refresh tokens."""
        token = "test_refresh_token"
        expires_at = timezone.now() + timedelta(days=7)
        session = Session.objects.create(
            user=self.user,
            refresh_token_hash=Session.hash_token(token),
            expires_at=expires_at
        )
        
        self.assertTrue(session.verify_token(token))
        self.assertFalse(session.verify_token("wrong_token"))
    
    def test_session_is_expired_property(self):
        """Test is_expired property."""
        # Future expiration
        future_session = Session.objects.create(
            user=self.user,
            refresh_token_hash="hash",
            expires_at=timezone.now() + timedelta(days=1)
        )
        self.assertFalse(future_session.is_expired)
        
        # Past expiration
        past_session = Session.objects.create(
            user=self.user,
            refresh_token_hash="hash2",
            expires_at=timezone.now() - timedelta(days=1)
        )
        self.assertTrue(past_session.is_expired)
    
    def test_session_is_valid_property(self):
        """Test is_valid property."""
        # Valid session
        valid_session = Session.objects.create(
            user=self.user,
            refresh_token_hash="hash",
            expires_at=timezone.now() + timedelta(days=1),
            revoked=False
        )
        self.assertTrue(valid_session.is_valid)
        
        # Revoked session
        revoked_session = Session.objects.create(
            user=self.user,
            refresh_token_hash="hash2",
            expires_at=timezone.now() + timedelta(days=1),
            revoked=True
        )
        self.assertFalse(revoked_session.is_valid)
        
        # Expired session
        expired_session = Session.objects.create(
            user=self.user,
            refresh_token_hash="hash3",
            expires_at=timezone.now() - timedelta(days=1)
        )
        self.assertFalse(expired_session.is_valid)


class PermissionModelTest(TestCase):
    """Test cases for Permission model."""
    
    def test_permission_creation(self):
        """Test creating a permission."""
        permission = Permission.objects.create(
            code="users.create",
            description="Can create users"
        )
        
        self.assertEqual(permission.code, "users.create")
        self.assertEqual(permission.description, "Can create users")
        self.assertIsInstance(permission.id, uuid.UUID)
    
    def test_permission_code_unique(self):
        """Test that permission code must be unique."""
        Permission.objects.create(code="users.create")
        with self.assertRaises(Exception):  # IntegrityError
            Permission.objects.create(code="users.create")
    
    def test_permission_str_representation(self):
        """Test string representation."""
        permission = Permission.objects.create(code="users.delete")
        self.assertEqual(str(permission), "users.delete")


class RolePermissionModelTest(TestCase):
    """Test cases for RolePermission model."""
    
    def setUp(self):
        """Set up test permissions."""
        self.perm1 = Permission.objects.create(code="users.create")
        self.perm2 = Permission.objects.create(code="users.delete")
        self.perm3 = Permission.objects.create(code="students.view")
    
    def test_role_permission_creation(self):
        """Test creating role-permission mapping."""
        role_perm = RolePermission.objects.create(
            role=RoleChoices.ADMIN,
            permission=self.perm1
        )
        
        self.assertEqual(role_perm.role, RoleChoices.ADMIN)
        self.assertEqual(role_perm.permission, self.perm1)
    
    def test_role_permission_unique_together(self):
        """Test that role-permission pairs must be unique."""
        RolePermission.objects.create(
            role=RoleChoices.ADMIN,
            permission=self.perm1
        )
        with self.assertRaises(Exception):  # IntegrityError
            RolePermission.objects.create(
                role=RoleChoices.ADMIN,
                permission=self.perm1
            )
    
    def test_get_permissions_for_role(self):
        """Test getting all permissions for a role."""
        RolePermission.objects.create(role=RoleChoices.ADMIN, permission=self.perm1)
        RolePermission.objects.create(role=RoleChoices.ADMIN, permission=self.perm2)
        RolePermission.objects.create(role=RoleChoices.STUDENT, permission=self.perm3)
        
        admin_perms = RolePermission.get_permissions_for_role(RoleChoices.ADMIN)
        
        self.assertEqual(len(admin_perms), 2)
        self.assertIn("users.create", admin_perms)
        self.assertIn("users.delete", admin_perms)
        self.assertNotIn("students.view", admin_perms)


class AuditLogModelTest(TestCase):
    """Test cases for AuditLog model."""
    
    def setUp(self):
        """Set up test user."""
        self.user = User.objects.create(email="test@example.com")
    
    def test_audit_log_creation(self):
        """Test creating an audit log entry."""
        log = AuditLog.objects.create(
            user=self.user,
            action="USER_LOGIN",
            entity="User",
            entity_id=self.user.id,
            details={"ip": "127.0.0.1"}
        )
        
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, "USER_LOGIN")
        self.assertEqual(log.entity, "User")
        self.assertEqual(log.details["ip"], "127.0.0.1")
        self.assertIsInstance(log.id, uuid.UUID)
    
    def test_audit_log_without_user(self):
        """Test creating audit log without user (system action)."""
        log = AuditLog.objects.create(
            action="SYSTEM_STARTUP",
            details={"version": "1.0"}
        )
        
        self.assertIsNone(log.user)
        self.assertEqual(log.action, "SYSTEM_STARTUP")
    
    def test_audit_log_class_method(self):
        """Test the log class method."""
        log = AuditLog.log(
            action="USER_CREATED",
            user=self.user,
            entity="User",
            entity_id=uuid.uuid4(),
            details={"email": "new@example.com"}
        )
        
        self.assertIsNotNone(log)
        self.assertEqual(log.action, "USER_CREATED")
        self.assertEqual(log.user, self.user)
    
    def test_audit_log_ordering(self):
        """Test that logs are ordered by created_at descending."""
        log1 = AuditLog.log(action="ACTION_1", user=self.user)
        log2 = AuditLog.log(action="ACTION_2", user=self.user)
        
        logs = list(AuditLog.objects.all())
        self.assertEqual(logs[0].action, "ACTION_2")
        self.assertEqual(logs[1].action, "ACTION_1")
