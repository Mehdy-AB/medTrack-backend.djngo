"""
Simple Role-Based Access Control (RBAC) Helper
===============================================

Provides simple decorators and utilities for role-based permissions.

Roles:
- student: Can view published content, create applications, mark attendance
- encadrant: Can create offers, manage applications, validate evaluations
- admin: Full access to everything
"""

from functools import wraps
from django.http import JsonResponse


def get_user_role(request):
    """Get the current user's role from request."""
    user_data = getattr(request, 'user_data', None)
    if not user_data:
        return None
    return user_data.get('role')


def get_user_id(request):
    """Get the current user's ID from request."""
    user_data = getattr(request, 'user_data', None)
    if not user_data:
        return None
    return user_data.get('user_id')


def require_roles(*allowed_roles):
    """
    Decorator to restrict access to specific roles.
    
    Usage:
        @require_roles('encadrant', 'admin')
        def create_offer(request):
            # Only encadrants and admins can access
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            role = get_user_role(request)
            
            if not role:
                return JsonResponse(
                    {'error': 'Authentication required'},
                    status=401
                )
            
            if role not in allowed_roles:
                return JsonResponse(
                    {
                        'error': 'Insufficient permissions',
                        'required_roles': list(allowed_roles),
                        'your_role': role
                    },
                    status=403
                )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def is_admin(request):
    """Check if current user is admin."""
    return get_user_role(request) == 'admin'


def is_encadrant(request):
    """Check if current user is encadrant."""
    return get_user_role(request) == 'encadrant'


def is_student(request):
    """Check if current user is student."""
    return get_user_role(request) == 'student'


def can_manage_offers(request):
    """Check if user can create/edit/delete offers."""
    role = get_user_role(request)
    return role in ['admin', 'encadrant']


def can_manage_applications(request):
    """Check if user can accept/reject applications."""
    role = get_user_role(request)
    return role in ['admin', 'encadrant']


def can_validate(request):
    """Check if user can validate attendance/evaluations."""
    role = get_user_role(request)
    return role in ['admin', 'encadrant']
