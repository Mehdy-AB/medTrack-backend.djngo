"""
JWT utilities for auth-service.
Handles access token and refresh token generation/validation.
"""
import jwt
import secrets
from datetime import datetime, timedelta, timezone
from django.conf import settings
from typing import Optional, Dict, Any


class JWTError(Exception):
    """Base exception for JWT errors."""
    pass


class TokenExpiredError(JWTError):
    """Token has expired."""
    pass


class InvalidTokenError(JWTError):
    """Token is invalid."""
    pass


def get_jwt_settings() -> Dict[str, Any]:
    """Get JWT configuration from settings."""
    return {
        'secret_key': getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY),
        'algorithm': getattr(settings, 'JWT_ALGORITHM', 'HS256'),
        'access_token_lifetime': getattr(settings, 'JWT_ACCESS_TOKEN_LIFETIME', timedelta(minutes=15)),
        'refresh_token_lifetime': getattr(settings, 'JWT_REFRESH_TOKEN_LIFETIME', timedelta(days=30)),
        'issuer': getattr(settings, 'JWT_ISSUER', 'auth-service'),
    }


def generate_access_token(user) -> str:
    """
    Generate JWT access token for user.
    
    Args:
        user: User model instance
        
    Returns:
        Encoded JWT access token string
    """
    jwt_settings = get_jwt_settings()
    now = datetime.now(timezone.utc)
    
    payload = {
        'sub': str(user.id),
        'email': user.email,
        'role': user.role,
        'type': 'access',
        'iat': now,
        'exp': now + jwt_settings['access_token_lifetime'],
        'iss': jwt_settings['issuer'],
    }
    
    return jwt.encode(
        payload,
        jwt_settings['secret_key'],
        algorithm=jwt_settings['algorithm']
    )


def generate_refresh_token(user, session_id: str) -> str:
    """
    Generate JWT refresh token for user.
    
    Args:
        user: User model instance
        session_id: Session UUID string
        
    Returns:
        Encoded JWT refresh token string
    """
    jwt_settings = get_jwt_settings()
    now = datetime.now(timezone.utc)
    
    payload = {
        'sub': str(user.id),
        'session_id': str(session_id),
        'type': 'refresh',
        'iat': now,
        'exp': now + jwt_settings['refresh_token_lifetime'],
        'iss': jwt_settings['issuer'],
    }
    
    return jwt.encode(
        payload,
        jwt_settings['secret_key'],
        algorithm=jwt_settings['algorithm']
    )


def decode_token(token: str, token_type: str = 'access') -> Dict[str, Any]:
    """
    Decode and validate JWT token.
    
    Args:
        token: JWT token string
        token_type: Expected token type ('access' or 'refresh')
        
    Returns:
        Decoded token payload
        
    Raises:
        TokenExpiredError: If token has expired
        InvalidTokenError: If token is invalid
    """
    jwt_settings = get_jwt_settings()
    
    try:
        payload = jwt.decode(
            token,
            jwt_settings['secret_key'],
            algorithms=[jwt_settings['algorithm']],
            issuer=jwt_settings['issuer']
        )
        
        # Verify token type
        if payload.get('type') != token_type:
            raise InvalidTokenError(f"Expected {token_type} token, got {payload.get('type')}")
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise InvalidTokenError(f"Invalid token: {str(e)}")


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate access token."""
    return decode_token(token, 'access')


def decode_refresh_token(token: str) -> Dict[str, Any]:
    """Decode and validate refresh token."""
    return decode_token(token, 'refresh')


def extract_token_from_header(auth_header: str) -> Optional[str]:
    """
    Extract JWT token from Authorization header.
    
    Args:
        auth_header: Authorization header value (e.g., "Bearer <token>")
        
    Returns:
        Token string or None if invalid format
    """
    if not auth_header:
        return None
    
    parts = auth_header.split()
    
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
    
    return parts[1]


def generate_random_token() -> str:
    """Generate a secure random token string."""
    return secrets.token_urlsafe(32)
