"""
Integration models for POSB Recruitment Portal.
Handles ERP exports and API key management.
"""
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator


class ERPExport(models.Model):
    """
    Tracks exports of shortlisted candidates to Dynamics 365 ERP.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    shortlisting_run = models.ForeignKey(
        'shortlisting.ShortlistingRun',
        on_delete=models.CASCADE,
        related_name='erp_exports'
    )
    job_advert = models.ForeignKey(
        'jobs.JobAdvert',
        on_delete=models.CASCADE,
        related_name='erp_exports'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    total_candidates = models.IntegerField(default=0)
    exported_count = models.IntegerField(default=0)
    failed_count = models.IntegerField(default=0)
    
    # ERP Response
    erp_batch_id = models.CharField(max_length=255, blank=True)
    erp_response = models.JSONField(default=dict, blank=True)
    
    # Error Handling
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    max_retries = models.IntegerField(default=3, validators=[MinValueValidator(0)])
    
    # Timestamps
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'erp_exports'
        verbose_name = 'ERP Export'
        verbose_name_plural = 'ERP Exports'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f'ERP Export for {self.job_advert.job_title} - {self.status}'


class ERPExportItem(models.Model):
    """
    Individual candidate export item within an ERP export batch.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('EXPORTED', 'Exported'),
        ('FAILED', 'Failed'),
    ]

    application = models.ForeignKey(
        'applications.Application',
        on_delete=models.CASCADE,
        related_name='erp_export_items'
    )
    export = models.ForeignKey(
        ERPExport,
        on_delete=models.CASCADE,
        related_name='items'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    erp_candidate_id = models.CharField(max_length=255, blank=True)
    error_message = models.TextField(blank=True)
    exported_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'erp_export_items'
        verbose_name = 'ERP Export Item'
        verbose_name_plural = 'ERP Export Items'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f'{self.application.applicant.email} - {self.status}'


class APIKey(models.Model):
    """
    API keys for external integrations (D365 job postings).
    """
    name = models.CharField(
        max_length=255,
        help_text='Descriptive name for this API key'
    )
    key = models.CharField(
        max_length=255,
        unique=True,
        help_text='The actual API key value'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this key is currently active'
    )
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_api_keys',
        help_text='User who created this key'
    )
    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Last time this key was used'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'api_keys'
        verbose_name = 'API Key'
        verbose_name_plural = 'API Keys'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['key', 'is_active']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f'{self.name} ({self.key[:8]}...)'

    def mark_used(self):
        """Mark this key as used (update last_used_at)."""
        self.last_used_at = timezone.now()
        self.save(update_fields=['last_used_at'])


class APIRequestLog(models.Model):
    """
    Logs all API requests for monitoring and debugging.
    """
    METHOD_CHOICES = [
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('DELETE', 'DELETE'),
        ('PATCH', 'PATCH'),
    ]

    STATUS_CHOICES = [
        ('SUCCESS', 'Success'),
        ('ERROR', 'Error'),
        ('VALIDATION_ERROR', 'Validation Error'),
        ('UNAUTHORIZED', 'Unauthorized'),
        ('RATE_LIMITED', 'Rate Limited'),
        ('NOT_FOUND', 'Not Found'),
        ('SERVER_ERROR', 'Server Error'),
    ]

    # Request details
    api_key = models.ForeignKey(
        APIKey,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='request_logs',
        help_text='API key used for this request'
    )
    method = models.CharField(
        max_length=10,
        choices=METHOD_CHOICES
    )
    endpoint = models.CharField(
        max_length=255,
        help_text='API endpoint path'
    )
    
    # Request data
    request_body = models.TextField(
        blank=True,
        help_text='Request payload (truncated if too long)'
    )
    request_headers = models.JSONField(
        default=dict,
        blank=True,
        help_text='Request headers (excluding sensitive data)'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='Client IP address'
    )
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        help_text='User agent string'
    )
    
    # Response details
    status_code = models.IntegerField(
        help_text='HTTP status code'
    )
    response_status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        help_text='Response status category'
    )
    response_body = models.TextField(
        blank=True,
        help_text='Response payload (truncated if too long)'
    )
    error_message = models.TextField(
        blank=True,
        help_text='Error message if request failed'
    )
    
    # Timing
    response_time_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text='Response time in milliseconds'
    )
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional context data'
    )
    
    timestamp = models.DateTimeField(
        default=timezone.now,
        db_index=True
    )

    class Meta:
        db_table = 'api_request_logs'
        verbose_name = 'API Request Log'
        verbose_name_plural = 'API Request Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['api_key', 'timestamp']),
            models.Index(fields=['status_code', 'timestamp']),
            models.Index(fields=['response_status', 'timestamp']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['endpoint', 'timestamp']),
        ]

    def __str__(self):
        return f'{self.method} {self.endpoint} - {self.status_code} ({self.timestamp})'
