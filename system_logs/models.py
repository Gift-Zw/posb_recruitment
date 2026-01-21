"""
System logging models for POSB Recruitment Portal.
Operational logs stored in database for monitoring and debugging.
"""
from django.db import models
from django.utils import timezone


class SystemLog(models.Model):
    """
    System log for operational events.
    Stores INFO, WARNING, ERROR level logs with stack traces.
    """
    LEVEL_CHOICES = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    SOURCE_CHOICES = [
        ('API', 'API'),
        ('CELERY', 'Celery Task'),
        ('INTEGRATION', 'External Integration'),
        ('SYSTEM', 'System'),
    ]
    
    level = models.CharField(
        max_length=10,
        choices=LEVEL_CHOICES,
        default='INFO'
    )
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='SYSTEM'
    )
    message = models.TextField(help_text='Log message')
    stack_trace = models.TextField(
        blank=True,
        help_text='Stack trace if error occurred'
    )
    
    # Context
    module = models.CharField(
        max_length=200,
        blank=True,
        help_text='Module/component where log originated'
    )
    function = models.CharField(
        max_length=200,
        blank=True,
        help_text='Function/method where log originated'
    )
    
    # Related entities (optional)
    related_user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='system_logs'
    )
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional context data'
    )
    
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    class Meta:
        db_table = 'system_logs'
        verbose_name = 'System Log'
        verbose_name_plural = 'System Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['level', 'timestamp']),
            models.Index(fields=['source', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f'{self.level} - {self.source} - {self.message[:50]}'
