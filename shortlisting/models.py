"""
AI Shortlisting models for POSB Recruitment Portal.
Tracks shortlisting runs and results.
"""
from django.db import models
from django.utils import timezone


class ShortlistingRun(models.Model):
    """
    Tracks each AI shortlisting execution for a job advert.
    Ensures auditability and traceability.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    job_advert = models.ForeignKey(
        'jobs.JobAdvert',
        on_delete=models.CASCADE,
        related_name='shortlisting_runs'
    )
    triggered_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='triggered_shortlisting_runs',
        help_text='User who triggered the shortlisting (null if automatic)'
    )
    trigger_type = models.CharField(
        max_length=20,
        choices=[
            ('AUTOMATIC', 'Automatic (after deadline)'),
            ('MANUAL', 'Manual (HR triggered)'),
        ],
        default='AUTOMATIC'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    
    # Configuration snapshot
    shortlist_count = models.IntegerField(
        help_text='Number of candidates to shortlist (snapshot at time of run)'
    )
    total_applications = models.IntegerField(
        default=0,
        help_text='Total applications processed'
    )
    shortlisted_count = models.IntegerField(
        default=0,
        help_text='Number of candidates actually shortlisted'
    )
    
    # Execution metadata
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, help_text='Error message if failed')
    
    # AI metadata
    ai_model_version = models.CharField(
        max_length=50,
        blank=True,
        help_text='Version/identifier of AI model used'
    )
    ai_configuration = models.JSONField(
        default=dict,
        blank=True,
        help_text='AI configuration parameters used'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'shortlisting_runs'
        verbose_name = 'Shortlisting Run'
        verbose_name_plural = 'Shortlisting Runs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['job_advert', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f'Shortlisting Run for {self.job_advert.title} - {self.status}'
