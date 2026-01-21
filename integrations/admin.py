"""
Admin configuration for integrations app.
"""
from django.contrib import admin
from .models import ERPExport, ERPExportItem


@admin.register(ERPExport)
class ERPExportAdmin(admin.ModelAdmin):
    list_display = ['job_advert', 'status', 'exported_count', 'failed_count', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['job_advert__title', 'erp_batch_id']
    readonly_fields = ['created_at', 'started_at', 'completed_at']
    fieldsets = (
        ('Export Information', {
            'fields': ('shortlisting_run', 'job_advert', 'status')
        }),
        ('Statistics', {
            'fields': ('total_candidates', 'exported_count', 'failed_count')
        }),
        ('ERP Response', {
            'fields': ('erp_batch_id', 'erp_response')
        }),
        ('Error Handling', {
            'fields': ('error_message', 'retry_count', 'max_retries')
        }),
        ('Timestamps', {
            'fields': ('started_at', 'completed_at', 'created_at')
        }),
    )


@admin.register(ERPExportItem)
class ERPExportItemAdmin(admin.ModelAdmin):
    list_display = ['application', 'export', 'status', 'erp_candidate_id', 'exported_at']
    list_filter = ['status', 'exported_at']
    search_fields = ['application__applicant__email', 'erp_candidate_id']
    readonly_fields = ['created_at', 'exported_at']
