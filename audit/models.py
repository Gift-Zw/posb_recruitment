"""
Audit logging models for POSB Recruitment Portal.
Immutable audit trail for all sensitive actions.
"""
from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class AuditLog(models.Model):
    """
    Immutable audit log for tracking all sensitive actions.
    Critical for compliance and security auditing.
    """
    ACTION_TYPES = [
        ('USER_REGISTRATION', 'User Registration'),
        ('OTP_VERIFICATION', 'OTP Verification'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('JOB_CREATED', 'Job Created'),
        ('JOB_UPDATED', 'Job Updated'),
        ('JOB_DELETED', 'Job Deleted'),
        ('APPLICATION_SUBMITTED', 'Application Submitted'),
        ('APPLICATION_UPDATED', 'Application Updated'),
        ('AI_SHORTLISTING', 'AI Shortlisting'),
        ('EMAIL_SENT', 'Email Sent'),
        ('ERP_EXPORT', 'ERP Export'),
        ('PROFILE_UPDATED', 'Profile Updated'),
        ('DOCUMENT_UPLOADED', 'Document Uploaded'),
        ('PASSWORD_CHANGED', 'Password Changed'),
    ]
    
    # Actor (who performed the action)
    actor = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        help_text='User who performed the action (null if system)'
    )
    actor_type = models.CharField(
        max_length=20,
        choices=[
            ('USER', 'User'),
            ('SYSTEM', 'System'),
            ('ADMIN', 'Admin'),
        ],
        default='USER'
    )
    
    # Action details
    action = models.CharField(
        max_length=50,
        choices=ACTION_TYPES
    )
    action_description = models.TextField(
        help_text='Human-readable description of the action'
    )
    
    # Entity being acted upon (generic foreign key)
    entity_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    entity_id = models.PositiveIntegerField(null=True, blank=True)
    entity = GenericForeignKey('entity_type', 'entity_id')
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional context data (IP address, user agent, etc.)'
    )
    
    # Timestamp (immutable)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    # Request context (if available)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    
    class Meta:
        db_table = 'audit_logs'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['actor', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        actor_str = self.actor.email if self.actor else self.actor_type
        return f'{actor_str} - {self.action} - {self.timestamp}'
    
    def save(self, *args, **kwargs):
        """Override save to prevent updates (immutable logs)."""
        if self.pk:
            raise ValueError('AuditLog entries are immutable and cannot be updated.')
        super().save(*args, **kwargs)
