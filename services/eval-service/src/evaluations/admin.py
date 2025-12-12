"""Admin configuration for evaluation models."""
from django.contrib import admin
from .models import Evaluation, EvaluationSection


class EvaluationSectionInline(admin.TabularInline):
    """Inline admin for evaluation sections."""
    model = EvaluationSection
    extra = 1


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    """Admin for evaluations."""
    list_display = ['student_id', 'offer_id', 'evaluator_id', 'grade', 'validated', 'submitted_at']
    list_filter = ['validated', 'submitted_at']
    search_fields = ['student_id', 'offer_id', 'evaluator_id']
    date_hierarchy = 'submitted_at'
    inlines = [EvaluationSectionInline]


@admin.register(EvaluationSection)
class EvaluationSectionAdmin(admin.ModelAdmin):
    """Admin for evaluation sections."""
    list_display = ['evaluation', 'criterion', 'score']
    list_filter = ['criterion']
    search_fields = ['criterion', 'evaluation__student_id']
