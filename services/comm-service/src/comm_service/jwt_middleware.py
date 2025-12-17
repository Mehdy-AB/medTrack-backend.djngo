"""
Shared JWT Middleware for Microservices
=======================================

This is a standalone JWT validation middleware that other services
(profile, core, eval, comm) can use to validate JWT tokens WITHOUT
calling the auth-service or accessing the user database.

USAGE:
1. Copy this file to your service
2. Set JWT_SECRET_KEY environment variable (same as auth-service)
3. Add JWTAuthMiddleware to MIDDLEWARE in settings.py

The middleware extracts and validates JWT tokens from the Authorization header
and adds user_data to the request object containing:
- user_id: UUID string
- email: User email
- role: User role (admin, student, encadrant)
"""
import os
import jwt
from datetime import datetime, timezone
from django.http import JsonResponse


class JWTError(Exception):
    """Base JWT error."""
    pass


class TokenExpiredError(JWTError):
    """Token has expired."""
    pass


class InvalidTokenError(JWTError):
    """Token is invalid."""
    pass


def get_jwt_config():
    """Get JWT configuration from environment."""
    return {
        'secret_key': os.environ.get('JWT_SECRET_KEY', os.environ.get('SECRET_KEY', '')),
        'algorithm': os.environ.get('JWT_ALGORITHM', 'HS256'),
        'issuer': 'auth-service',
    }


def decode_access_token(token: str) -> dict:
    """
    Decode and validate JWT access token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload with user_id, email, role
        
    Raises:
        TokenExpiredError: If token expired
        InvalidTokenError: If token invalid
    """
    config = get_jwt_config()
    
    try:
        payload = jwt.decode(
            token,
            config['secret_key'],
            algorithms=[config['algorithm']],
            issuer=config['issuer']
        )
        
        if payload.get('type') != 'access':
            raise InvalidTokenError("Not an access token")
        
        return {
            'user_id': payload.get('sub'),
            'email': payload.get('email'),
            'role': payload.get('role'),
        }
        
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise InvalidTokenError(f"Invalid token: {str(e)}")


def extract_token_from_header(auth_header: str) -> str:
    """Extract Bearer token from Authorization header."""
    if not auth_header:
        return None
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
    
    return parts[1]


class JWTAuthMiddleware:
    """
    JWT Authentication Middleware for Django.
    
    Validates JWT tokens and adds user_data to request.
    Skips authentication for paths in EXEMPT_PATHS.
    """
    
    # Paths that don't require authentication
    EXEMPT_PATHS = [
        '/health',
        '/metrics',
        '/comm/health',
        '/comm/',  # Allow internal service-to-service calls
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip authentication for exempt paths
        path = request.path.rstrip('/')
        if any(path.startswith(exempt.rstrip('/')) for exempt in self.EXEMPT_PATHS):
            request.user_data = None
            return self.get_response(request)
        
        # Skip OPTIONS requests (CORS preflight)
        if request.method == 'OPTIONS':
            return self.get_response(request)
        
        # Extract token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        token = extract_token_from_header(auth_header)
        
        if not token:
            return JsonResponse(
                {'error': 'Authorization header required', 'code': 'NO_TOKEN'},
                status=401
            )
        
        try:
            # Decode and validate token
            request.user_data = decode_access_token(token)
            return self.get_response(request)
            
        except TokenExpiredError:
            return JsonResponse(
                {'error': 'Token has expired', 'code': 'TOKEN_EXPIRED'},
                status=401
            )
        except InvalidTokenError:
            return JsonResponse(
                {'error': 'Invalid token', 'code': 'INVALID_TOKEN'},
                status=401
            )


def require_role(*allowed_roles):
    """
    Decorator to require specific roles for a view.
    
    Usage:
        @require_role('admin')
        def admin_only_view(request):
            ...
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            user_data = getattr(request, 'user_data', None)
            if not user_data:
                return JsonResponse(
                    {'error': 'Authentication required', 'code': 'AUTH_REQUIRED'},
                    status=401
                )
            
            if user_data.get('role') not in allowed_roles:
                return JsonResponse(
                    {'error': 'Insufficient permissions', 'code': 'FORBIDDEN'},
                    status=403
                )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def get_current_user_id(request) -> str:
    """Get current user ID from request."""
    user_data = getattr(request, 'user_data', None)
    return user_data.get('user_id') if user_data else None


def get_current_user_role(request) -> str:
    """Get current user role from request."""
    user_data = getattr(request, 'user_data', None)
    return user_data.get('role') if user_data else None
