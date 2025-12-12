"""Admin configuration for affectations app."""
from django.contrib import admin
from .models import Affectation


@admin.register(Affectation)
class AffectationAdmin(admin.ModelAdmin):
    """Admin for Affectation model."""
    list_display = ['id', 'student_id', 'offer', 'application', 'assigned_at']
    list_filter = ['assigned_at']
    search_fields = ['student_id', 'offer__title']
    readonly_fields = ['id', 'assigned_at']
