"""
Serializers for auth-service API.
"""
from rest_framework import serializers
from .models import User, Session, Permission, RolePermission, AuditLog, RoleChoices


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model (public fields only)."""
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'phone',
            'role', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserCreateSerializer(serializers.Serializer):
    """Serializer for user registration."""
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(min_length=6, write_only=True)
    first_name = serializers.CharField(max_length=120, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=120, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=RoleChoices.choices, required=False, default='student')
    
    def validate_email(self, value):
        """Check email is unique."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email already registered")
        return value.lower()
    
    def create(self, validated_data):
        """Create new user with hashed password."""
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for login request."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class TokenResponseSerializer(serializers.Serializer):
    """Serializer for token response."""
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    token_type = serializers.CharField(default='Bearer')
    expires_in = serializers.IntegerField()


class RefreshTokenSerializer(serializers.Serializer):
    """Serializer for refresh token request."""
    refresh_token = serializers.CharField()


class UpdateProfileSerializer(serializers.Serializer):
    """Serializer for updating user profile."""
    first_name = serializers.CharField(max_length=120, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=120, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password."""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(min_length=6, write_only=True)


class UserUpdateSerializer(serializers.Serializer):
    """Serializer for admin user update."""
    first_name = serializers.CharField(max_length=120, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=120, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=RoleChoices.choices, required=False)
    is_active = serializers.BooleanField(required=False)


class SessionSerializer(serializers.ModelSerializer):
    """Serializer for Session model."""
    
    class Meta:
        model = Session
        fields = ['id', 'issued_at', 'expires_at', 'client_info', 'revoked']
        read_only_fields = ['id', 'issued_at', 'expires_at', 'revoked']


class PermissionSerializer(serializers.ModelSerializer):
    """Serializer for Permission model."""
    
    class Meta:
        model = Permission
        fields = ['id', 'code', 'description']


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for AuditLog model."""
    user_email = serializers.SerializerMethodField()
    
    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'user_email', 'action', 'entity', 'entity_id', 'details', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_user_email(self, obj):
        return obj.user.email if obj.user else None


class AuthResponseSerializer(serializers.Serializer):
    """Full auth response with tokens and user."""
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    token_type = serializers.CharField(default='Bearer')
    expires_in = serializers.IntegerField()
    user = UserSerializer()
