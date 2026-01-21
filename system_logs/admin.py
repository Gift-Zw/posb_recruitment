"""
Admin configuration for system_logs app.
"""
from django.contrib import admin
from .models import SystemLog


@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ['level', 'source', 'message', 'module', 'timestamp']
    list_filter = ['level', 'source', 'timestamp']
    search_fields = ['message', 'module', 'function']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Log Details', {
            'fields': ('level', 'source', 'message')
        }),
        ('Context', {
            'fields': ('module', 'function', 'related_user')
        }),
        ('Error Details', {
            'fields': ('stack_trace',),
            'classes': ('collapse',)
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
        """Prevent manual creation of system logs."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent modification of system logs."""
        return False
