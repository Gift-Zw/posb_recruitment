"""
Admin configuration for notifications app.
"""
from django.contrib import admin
from .models import EmailNotification


@admin.register(EmailNotification)
class EmailNotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'notification_type', 'status', 'sent_at', 'created_at']
    list_filter = ['notification_type', 'status', 'created_at']
    search_fields = ['recipient__email', 'subject']
    readonly_fields = ['created_at', 'sent_at']
    fieldsets = (
        ('Notification Details', {
            'fields': ('recipient', 'notification_type', 'subject', 'message')
        }),
        ('Status', {
            'fields': ('status', 'sent_at', 'error_message', 'retry_count')
        }),
        ('Related Entities', {
            'fields': ('related_application', 'related_otp')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )
