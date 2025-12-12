"""Admin configuration for attendance models."""
from django.contrib import admin
from .models import AttendanceRecord, AttendanceSummary


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    """Admin for attendance records."""
    list_display = ['student_id', 'offer_id', 'date', 'is_present', 'justified', 'marked_at']
    list_filter = ['is_present', 'justified', 'date']
    search_fields = ['student_id', 'offer_id']
    date_hierarchy = 'date'


@admin.register(AttendanceSummary)
class AttendanceSummaryAdmin(admin.ModelAdmin):
    """Admin for attendance summaries."""
    list_display = ['student_id', 'offer_id', 'total_days', 'present_days', 'presence_rate', 'validated']
    list_filter = ['validated']
    search_fields = ['student_id', 'offer_id']
    readonly_fields = ['presence_rate']
