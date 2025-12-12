"""
API Views for auth-service.
"""
import logging
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import User, Session, Permission, AuditLog, RoleChoices
from .serializers import (
    UserSerializer, UserCreateSerializer, LoginSerializer,
    RefreshTokenSerializer, UpdateProfileSerializer, ChangePasswordSerializer,
    UserUpdateSerializer, SessionSerializer, AuditLogSerializer,
    PermissionSerializer
)
from auth_service.jwt_utils import (
    generate_access_token, generate_refresh_token,
    decode_refresh_token, InvalidTokenError, TokenExpiredError
)
from auth_service.middleware import get_current_user, require_auth, require_role
from auth_service.events import (
    publish_user_created, publish_user_updated, publish_user_role_changed,
    publish_session_revoked, publish_password_changed, publish_user_deleted
)

logger = logging.getLogger(__name__)


def get_tokens_response(user, request=None):
    """Generate tokens and create session for user."""
    # Create session
    refresh_token_raw = generate_refresh_token(user, 'temp')
    
    session = Session.objects.create(
        user=user,
        refresh_token_hash=Session.hash_token(refresh_token_raw),
        expires_at=timezone.now() + settings.JWT_REFRESH_TOKEN_LIFETIME,
        client_info={
            'user_agent': request.META.get('HTTP_USER_AGENT', '') if request else '',
            'ip': request.META.get('REMOTE_ADDR', '') if request else '',
        }
    )
    
    # Generate proper refresh token with session ID
    refresh_token = generate_refresh_token(user, str(session.id))
    session.refresh_token_hash = Session.hash_token(refresh_token)
    session.save()
    
    access_token = generate_access_token(user)
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in': int(settings.JWT_ACCESS_TOKEN_LIFETIME.total_seconds()),
        'user': UserSerializer(user).data
    }


# ============================================
# PUBLIC ENDPOINTS (no auth required)
# ============================================

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    POST /auth/api/v1/login
    Authenticate user and return tokens.
    """
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data['email'].lower()
    password = serializer.validated_data['password']
    
    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        AuditLog.log('LOGIN_FAILED', action='Invalid credentials', details={'email': email})
        return Response(
            {'error': 'Invalid credentials', 'code': 'INVALID_CREDENTIALS'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if not user.is_active:
        AuditLog.log('LOGIN_FAILED', user=user, action='Account disabled')
        return Response(
            {'error': 'Account is disabled', 'code': 'ACCOUNT_DISABLED'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if not user.check_password(password):
        AuditLog.log('LOGIN_FAILED', user=user, action='Invalid password')
        return Response(
            {'error': 'Invalid credentials', 'code': 'INVALID_CREDENTIALS'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Generate tokens
    response_data = get_tokens_response(user, request)
    
    AuditLog.log('LOGIN_SUCCESS', user=user, action='User logged in')
    
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    POST /auth/api/v1/register
    Register new user and return tokens.
    """
    serializer = UserCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    user = serializer.save()
    
    # Publish event
    publish_user_created(user)
    
    # Generate tokens
    response_data = get_tokens_response(user, request)
    
    AuditLog.log(
        'USER_REGISTERED',
        user=user,
        action='User registered',
        entity='User',
        entity_id=user.id
    )
    
    return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """
    POST /auth/api/v1/refresh
    Refresh access token using refresh token.
    """
    serializer = RefreshTokenSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    token = serializer.validated_data['refresh_token']
    
    try:
        payload = decode_refresh_token(token)
    except (InvalidTokenError, TokenExpiredError) as e:
        return Response(
            {'error': str(e), 'code': 'INVALID_REFRESH_TOKEN'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    session_id = payload.get('session_id')
    user_id = payload.get('sub')
    
    try:
        session = Session.objects.get(id=session_id, user_id=user_id)
    except Session.DoesNotExist:
        return Response(
            {'error': 'Session not found', 'code': 'SESSION_NOT_FOUND'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if not session.is_valid:
        return Response(
            {'error': 'Session expired or revoked', 'code': 'SESSION_INVALID'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    user = session.user
    if not user.is_active:
        return Response(
            {'error': 'Account is disabled', 'code': 'ACCOUNT_DISABLED'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Generate new access token only
    access_token = generate_access_token(user)
    
    return Response({
        'access_token': access_token,
        'token_type': 'Bearer',
        'expires_in': int(settings.JWT_ACCESS_TOKEN_LIFETIME.total_seconds()),
    })


# ============================================
# AUTHENTICATED USER ENDPOINTS
# ============================================

@api_view(['GET', 'PATCH'])
def current_user(request):
    """
    GET/PATCH /auth/api/v1/users/me
    Get or update current user profile.
    """
    user = get_current_user(request)
    if not user:
        return Response(
            {'error': 'User not found', 'code': 'USER_NOT_FOUND'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if request.method == 'GET':
        return Response(UserSerializer(user).data)
    
    # PATCH
    serializer = UpdateProfileSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    changed_fields = []
    for field, value in serializer.validated_data.items():
        if getattr(user, field) != value:
            setattr(user, field, value)
            changed_fields.append(field)
    
    if changed_fields:
        user.save()
        publish_user_updated(user, changed_fields)
        AuditLog.log(
            'PROFILE_UPDATED',
            user=user,
            action='Profile updated',
            entity='User',
            entity_id=user.id,
            details={'changed_fields': changed_fields}
        )
    
    return Response(UserSerializer(user).data)


@api_view(['PATCH'])
def change_password(request):
    """
    PATCH /auth/api/v1/users/me/password
    Change current user password.
    """
    user = get_current_user(request)
    if not user:
        return Response(
            {'error': 'User not found', 'code': 'USER_NOT_FOUND'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = ChangePasswordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    if not user.check_password(serializer.validated_data['old_password']):
        return Response(
            {'error': 'Current password is incorrect', 'code': 'INVALID_PASSWORD'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user.set_password(serializer.validated_data['new_password'])
    user.save()
    
    # Revoke all other sessions
    Session.objects.filter(user=user, revoked=False).update(revoked=True)
    
    publish_password_changed(user)
    AuditLog.log(
        'PASSWORD_CHANGED',
        user=user,
        action='Password changed',
        entity='User',
        entity_id=user.id
    )
    
    # Generate new tokens
    response_data = get_tokens_response(user, request)
    
    return Response(response_data)


# ============================================
# ADMIN USER MANAGEMENT ENDPOINTS
# ============================================

class UserPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET'])
def list_users(request):
    """
    GET /auth/api/v1/users
    List all users with pagination and filtering.
    """
    user_data = getattr(request, 'user_data', {})
    if user_data.get('role') != 'admin':
        return Response(
            {'error': 'Admin access required', 'code': 'FORBIDDEN'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    queryset = User.objects.all()
    
    # Filtering
    role = request.query_params.get('role')
    if role:
        queryset = queryset.filter(role=role)
    
    search = request.query_params.get('search')
    if search:
        queryset = queryset.filter(
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    is_active = request.query_params.get('is_active')
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active.lower() == 'true')
    
    # Pagination
    paginator = UserPagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = UserSerializer(page, many=True)
    
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET', 'PATCH', 'DELETE'])
def user_detail(request, user_id):
    """
    GET/PATCH/DELETE /auth/api/v1/users/{id}
    Manage specific user (admin only).
    """
    user_data = getattr(request, 'user_data', {})
    if user_data.get('role') != 'admin':
        return Response(
            {'error': 'Admin access required', 'code': 'FORBIDDEN'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found', 'code': 'USER_NOT_FOUND'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if request.method == 'GET':
        return Response(UserSerializer(user).data)
    
    if request.method == 'DELETE':
        email = user.email
        user_id_str = str(user.id)
        user.delete()
        publish_user_deleted(user_id_str, email)
        AuditLog.log(
            'USER_DELETED',
            user=get_current_user(request),
            action='User deleted',
            entity='User',
            entity_id=user_id,
            details={'deleted_email': email}
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    # PATCH
    serializer = UserUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    old_role = user.role
    changed_fields = []
    
    for field, value in serializer.validated_data.items():
        if getattr(user, field) != value:
            setattr(user, field, value)
            changed_fields.append(field)
    
    if changed_fields:
        user.save()
        
        if 'role' in changed_fields:
            publish_user_role_changed(user, old_role, user.role)
        else:
            publish_user_updated(user, changed_fields)
        
        AuditLog.log(
            'USER_UPDATED',
            user=get_current_user(request),
            action='User updated by admin',
            entity='User',
            entity_id=user.id,
            details={'changed_fields': changed_fields}
        )
    
    return Response(UserSerializer(user).data)


# ============================================
# SESSION MANAGEMENT ENDPOINTS
# ============================================

@api_view(['GET'])
def list_sessions(request):
    """
    GET /auth/api/v1/sessions
    List current user's sessions.
    """
    user = get_current_user(request)
    if not user:
        return Response(
            {'error': 'User not found', 'code': 'USER_NOT_FOUND'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    sessions = Session.objects.filter(user=user, revoked=False)
    serializer = SessionSerializer(sessions, many=True)
    
    return Response(serializer.data)


@api_view(['DELETE'])
def revoke_session(request, session_id):
    """
    DELETE /auth/api/v1/sessions/{id}
    Revoke a specific session.
    """
    user = get_current_user(request)
    if not user:
        return Response(
            {'error': 'User not found', 'code': 'USER_NOT_FOUND'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        session = Session.objects.get(id=session_id, user=user)
    except Session.DoesNotExist:
        return Response(
            {'error': 'Session not found', 'code': 'SESSION_NOT_FOUND'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    session.revoked = True
    session.save()
    
    publish_session_revoked(session, user)
    AuditLog.log(
        'SESSION_REVOKED',
        user=user,
        action='Session revoked',
        entity='Session',
        entity_id=session.id
    )
    
    return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================
# AUDIT LOG ENDPOINTS
# ============================================

class AuditLogPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


@api_view(['GET'])
def list_audit_logs(request):
    """
    GET /auth/api/v1/audit-logs
    List audit logs (admin only).
    """
    user_data = getattr(request, 'user_data', {})
    if user_data.get('role') != 'admin':
        return Response(
            {'error': 'Admin access required', 'code': 'FORBIDDEN'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    queryset = AuditLog.objects.all().select_related('user')
    
    # Filtering
    user_id = request.query_params.get('user_id')
    if user_id:
        queryset = queryset.filter(user_id=user_id)
    
    action = request.query_params.get('action')
    if action:
        queryset = queryset.filter(action__icontains=action)
    
    entity = request.query_params.get('entity')
    if entity:
        queryset = queryset.filter(entity=entity)
    
    # Pagination
    paginator = AuditLogPagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = AuditLogSerializer(page, many=True)
    
    return paginator.get_paginated_response(serializer.data)


# ============================================
# PERMISSIONS ENDPOINTS
# ============================================

@api_view(['GET'])
def list_permissions(request):
    """
    GET /auth/api/v1/permissions
    List all permissions.
    """
    permissions = Permission.objects.all()
    serializer = PermissionSerializer(permissions, many=True)
    return Response(serializer.data)
