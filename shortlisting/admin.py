"""
Admin configuration for shortlisting app.
"""
from django.contrib import admin
from .models import ShortlistingRun


@admin.register(ShortlistingRun)
class ShortlistingRunAdmin(admin.ModelAdmin):
    list_display = ['job_advert', 'trigger_type', 'status', 'shortlisted_count', 'total_applications', 'created_at']
    list_filter = ['status', 'trigger_type', 'created_at']
    search_fields = ['job_advert__title']
    readonly_fields = ['created_at', 'started_at', 'completed_at']
    fieldsets = (
        ('Run Information', {
            'fields': ('job_advert', 'triggered_by', 'trigger_type', 'status')
        }),
        ('Results', {
            'fields': ('shortlist_count', 'total_applications', 'shortlisted_count')
        }),
        ('Execution', {
            'fields': ('started_at', 'completed_at', 'error_message')
        }),
        ('AI Configuration', {
            'fields': ('ai_model_version', 'ai_configuration'),
            'classes': ('collapse',)
        }),
    )
