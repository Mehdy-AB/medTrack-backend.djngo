"""Admin configuration for applications app."""
from django.contrib import admin
from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    """Admin for Application model."""
    list_display = ['id', 'student_id', 'offer', 'status', 'submitted_at', 'decision_at']
    list_filter = ['status', 'submitted_at']
    search_fields = ['student_id', 'offer__title']
    readonly_fields = ['id', 'submitted_at', 'decision_at', 'decision_by']
