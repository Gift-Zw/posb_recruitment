"""
Integration models for POSB Recruitment Portal.
Tracks Dynamics 365 ERP integration and other external system interactions.
"""
from django.db import models
from django.utils import timezone


class ERPExport(models.Model):
    """
    Tracks exports of shortlisted candidates to Dynamics 365 ERP.
    Ensures traceability and handles retries.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('PARTIAL', 'Partial Success'),
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
    
    # Export statistics
    total_candidates = models.IntegerField(default=0)
    exported_count = models.IntegerField(default=0)
    failed_count = models.IntegerField(default=0)
    
    # ERP response
    erp_batch_id = models.CharField(
        max_length=255,
        blank=True,
        help_text='Batch ID returned by Dynamics 365'
    )
    erp_response = models.JSONField(
        default=dict,
        blank=True,
        help_text='Full response from Dynamics 365 API'
    )
    
    # Error handling
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    
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
            models.Index(fields=['job_advert', 'status']),
        ]
    
    def __str__(self):
        return f'ERP Export for {self.job_advert.title} - {self.status}'


class ERPExportItem(models.Model):
    """
    Individual candidate export item within an ERP export batch.
    Tracks per-candidate export status and ERP reference IDs.
    """
    export = models.ForeignKey(
        ERPExport,
        on_delete=models.CASCADE,
        related_name='export_items'
    )
    application = models.ForeignKey(
        'applications.Application',
        on_delete=models.CASCADE,
        related_name='erp_export_items'
    )
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('EXPORTED', 'Exported'),
            ('FAILED', 'Failed'),
        ],
        default='PENDING'
    )
    
    # ERP reference
    erp_candidate_id = models.CharField(
        max_length=255,
        blank=True,
        help_text='Candidate ID in Dynamics 365'
    )
    erp_document_id = models.CharField(
        max_length=255,
        blank=True,
        help_text='Document ID in Dynamics 365'
    )
    
    # Error tracking
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    
    # Timestamps
    exported_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'erp_export_items'
        verbose_name = 'ERP Export Item'
        verbose_name_plural = 'ERP Export Items'
        ordering = ['-created_at']
        unique_together = [['export', 'application']]
        indexes = [
            models.Index(fields=['export', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f'{self.application.applicant.email} - {self.status}'
