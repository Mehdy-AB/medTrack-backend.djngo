"""Django app configuration for applications."""
from django.apps import AppConfig


class ApplicationsConfig(AppConfig):
    """Configuration for applications app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'applications'
