"""
Admin configuration for integrations app.
"""
import secrets
from django.contrib import admin
from django.utils.html import format_html
from .models import ERPExport, ERPExportItem, APIKey, APIRequestLog


@admin.register(ERPExport)
class ERPExportAdmin(admin.ModelAdmin):
    list_display = ['job_advert', 'status', 'exported_count', 'failed_count', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['job_advert__job_title', 'erp_batch_id']
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


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ['name', 'key_preview', 'is_active', 'last_used_at', 'created_at', 'created_by']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'key']
    readonly_fields = ['key', 'created_at', 'updated_at', 'last_used_at']
    fieldsets = (
        ('Key Information', {
            'fields': ('name', 'key', 'is_active')
        }),
        ('Usage', {
            'fields': ('last_used_at',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )
    
    def key_preview(self, obj):
        """Show masked key preview."""
        if obj.key:
            return format_html('<code>{}</code>', obj.key[:8] + '...' + obj.key[-4:])
        return '-'
    key_preview.short_description = 'Key Preview'
    
    def save_model(self, request, obj, form, change):
        """Generate API key if creating new."""
        if not change:  # Creating new
            # Generate a secure random key
            obj.key = secrets.token_urlsafe(32)
            if not obj.created_by:
                obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_readonly_fields(self, request, obj=None):
        """Make key readonly after creation."""
        if obj:  # Editing existing
            return self.readonly_fields
        return ['created_at', 'updated_at', 'last_used_at']


@admin.register(APIRequestLog)
class APIRequestLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'method', 'endpoint', 'api_key', 'status_code', 'response_status', 'response_time_ms', 'ip_address']
    list_filter = ['method', 'status_code', 'response_status', 'timestamp']
    search_fields = ['endpoint', 'ip_address', 'api_key__name', 'api_key__key']
    readonly_fields = ['timestamp', 'api_key', 'method', 'endpoint', 'request_body', 'request_headers', 
                      'ip_address', 'user_agent', 'status_code', 'response_status', 'response_body', 
                      'error_message', 'response_time_ms', 'metadata']
    fieldsets = (
        ('Request Details', {
            'fields': ('timestamp', 'api_key', 'method', 'endpoint', 'ip_address', 'user_agent')
        }),
        ('Request Data', {
            'fields': ('request_body', 'request_headers')
        }),
        ('Response Details', {
            'fields': ('status_code', 'response_status', 'response_body', 'error_message', 'response_time_ms')
        }),
        ('Metadata', {
            'fields': ('metadata',)
        }),
    )
    
    def has_add_permission(self, request):
        """Disable manual creation of logs."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Make logs read-only."""
        return False

