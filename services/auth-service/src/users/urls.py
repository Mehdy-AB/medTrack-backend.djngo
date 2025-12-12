"""
URL configuration for users app.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Public endpoints
    path('login', views.login, name='login'),
    path('register', views.register, name='register'),
    path('refresh', views.refresh_token, name='refresh'),
    
    # Current user endpoints
    path('users/me', views.current_user, name='current-user'),
    path('users/me/password', views.change_password, name='change-password'),
    
    # Admin user management
    path('users', views.list_users, name='list-users'),
    path('users/<uuid:user_id>', views.user_detail, name='user-detail'),
    
    # Session management
    path('sessions', views.list_sessions, name='list-sessions'),
    path('sessions/<uuid:session_id>', views.revoke_session, name='revoke-session'),
    
    # Audit logs
    path('audit-logs', views.list_audit_logs, name='list-audit-logs'),
    
    # Permissions
    path('permissions', views.list_permissions, name='list-permissions'),
]
