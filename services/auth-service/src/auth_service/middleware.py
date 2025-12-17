"""
JWT Authentication Middleware for auth-service.
"""
import logging
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from .jwt_utils import decode_access_token, extract_token_from_header, TokenExpiredError, InvalidTokenError

logger = logging.getLogger(__name__)


class JWTAuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware to authenticate requests using JWT tokens.
    Extracts user info from token and adds to request.
    """
    
    # Paths that don't require authentication
    EXEMPT_PATHS = [
        '/health',
        '/metrics',
        '/auth/health',
        '/auth/api/v1/login',
        '/auth/api/v1/register',
        '/auth/api/v1/refresh',
        '/auth/api/v1/users/',  # Allow internal service-to-service user lookups
    ]
    
    def process_request(self, request):
        """Process incoming request and validate JWT if required."""
        # Skip authentication for exempt paths
        path = request.path.rstrip('/')
        if any(path.startswith(exempt.rstrip('/')) for exempt in self.EXEMPT_PATHS):
            request.user_data = None
            return None
        
        # Skip OPTIONS requests (CORS preflight)
        if request.method == 'OPTIONS':
            return None
        
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
            payload = decode_access_token(token)
            
            # Add user data to request
            request.user_data = {
                'user_id': payload.get('sub'),
                'email': payload.get('email'),
                'role': payload.get('role'),
            }
            
            return None
            
        except TokenExpiredError:
            return JsonResponse(
                {'error': 'Token has expired', 'code': 'TOKEN_EXPIRED'},
                status=401
            )
        except InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return JsonResponse(
                {'error': 'Invalid token', 'code': 'INVALID_TOKEN'},
                status=401
            )


def get_current_user(request):
    """
    Get current user from request.
    
    Returns:
        User instance or None
    """
    user_data = getattr(request, 'user_data', None)
    if not user_data or not user_data.get('user_id'):
        return None
    
    from users.models import User
    try:
        return User.objects.get(id=user_data['user_id'], is_active=True)
    except User.DoesNotExist:
        return None


def require_auth(view_func):
    """Decorator to require authentication for a view."""
    def wrapper(request, *args, **kwargs):
        user_data = getattr(request, 'user_data', None)
        if not user_data:
            return JsonResponse(
                {'error': 'Authentication required', 'code': 'AUTH_REQUIRED'},
                status=401
            )
        return view_func(request, *args, **kwargs)
    return wrapper


def require_role(*allowed_roles):
    """Decorator to require specific roles for a view."""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            user_data = getattr(request, 'user_data', None)
            if not user_data:
                return JsonResponse(
                    {'error': 'Authentication required', 'code': 'AUTH_REQUIRED'},
                    status=401
                )
            
            user_role = user_data.get('role')
            if user_role not in allowed_roles:
                return JsonResponse(
                    {'error': 'Insufficient permissions', 'code': 'FORBIDDEN'},
                    status=403
                )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
