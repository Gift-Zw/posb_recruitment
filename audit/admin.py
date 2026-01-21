"""
Admin configuration for audit app.
"""
from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['actor', 'actor_type', 'action', 'timestamp', 'ip_address']
    list_filter = ['action', 'actor_type', 'timestamp']
    search_fields = ['action_description', 'actor__email', 'ip_address']
    readonly_fields = ['timestamp', 'actor', 'action', 'action_description', 'metadata']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Actor', {
            'fields': ('actor', 'actor_type')
        }),
        ('Action', {
            'fields': ('action', 'action_description')
        }),
        ('Entity', {
            'fields': ('entity_type', 'entity_id')
        }),
        ('Context', {
            'fields': ('ip_address', 'user_agent', 'request_path')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('timestamp',)
        }),
    )
    
    def has_add_permission(self, request):
        """Prevent manual creation of audit logs."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent modification of audit logs (immutable)."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of audit logs (compliance requirement)."""
        return False
