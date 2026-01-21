"""
Job management models for POSB Recruitment Portal.
Job categories, adverts, and required skills.
"""
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator


class JobCategory(models.Model):
    """Job category classification."""
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'job_categories'
        verbose_name = 'Job Category'
        verbose_name_plural = 'Job Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Skill(models.Model):
    """Skill model for job requirements and applicant profiles."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'skills'
        verbose_name = 'Skill'
        verbose_name_plural = 'Skills'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class JobAdvert(models.Model):
    """
    Job advertisement model.
    Includes AI shortlisting configuration and application deadline.
    """
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
    ]
    
    CONTRACT_TYPE_CHOICES = [
        ('PERMANENT', 'Permanent'),
        ('FIXED_TERM', 'Fixed-Term'),
        ('INTERNSHIP', 'Internship'),
        ('PART_TIME', 'Part-Time'),
        ('CASUAL', 'Casual'),
    ]
    
    EDUCATION_LEVEL_CHOICES = [
        ('DEGREE', 'Degree'),
        ('DIPLOMA', 'Diploma'),
        ('CERTIFICATION', 'Certification'),
        ('HIGH_SCHOOL', 'High School'),
        ('NONE', 'No Specific Requirement'),
    ]
    
    LOCATION_TYPE_CHOICES = [
        ('BRANCH', 'Branch'),
        ('CITY', 'City'),
        ('REMOTE', 'Remote'),
        ('HYBRID', 'Hybrid'),
    ]
    
    title = models.CharField(max_length=300)
    category = models.ForeignKey(
        JobCategory,
        on_delete=models.PROTECT,
        related_name='job_adverts'
    )
    description = models.TextField(help_text='Full job description')
    responsibilities = models.TextField(help_text='Key responsibilities and duties')
    
    # Location
    location_type = models.CharField(
        max_length=20,
        choices=LOCATION_TYPE_CHOICES,
        default='BRANCH',
        help_text='Type of work location'
    )
    location = models.CharField(
        max_length=200,
        blank=True,
        help_text='Specific location (branch name, city, or "Remote" for remote positions)'
    )
    
    # Contract and Requirements
    contract_type = models.CharField(
        max_length=20,
        choices=CONTRACT_TYPE_CHOICES,
        default='PERMANENT',
        help_text='Type of employment contract'
    )
    education_level = models.CharField(
        max_length=20,
        choices=EDUCATION_LEVEL_CHOICES,
        blank=True,
        help_text='Minimum education level required'
    )
    experience_required = models.TextField(
        blank=True,
        help_text='Experience requirements (e.g., "2 years in banking", "5 years customer service")'
    )
    
    # Required skills
    required_skills = models.ManyToManyField(
        Skill,
        related_name='job_adverts',
        blank=True,
        help_text='Skills required for this position'
    )
    
    # Application settings
    application_deadline = models.DateTimeField(
        help_text='Deadline for accepting applications'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT',
        help_text='Current status of the job advert'
    )
    
    # AI Shortlisting configuration
    shortlist_count = models.IntegerField(
        default=10,
        validators=[MinValueValidator(1)],
        help_text='Number of candidates to shortlist'
    )
    ai_shortlisting_instructions = models.TextField(
        blank=True,
        help_text='Custom instructions for AI shortlisting algorithm'
    )
    
    # Metadata
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_job_adverts'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'job_adverts'
        verbose_name = 'Job Advert'
        verbose_name_plural = 'Job Adverts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'application_deadline']),
            models.Index(fields=['category']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f'{self.title} - {self.category.name}'
    
    def is_open_for_applications(self):
        """Check if job is open and accepting applications."""
        if self.status != 'OPEN':
            return False
        if timezone.now() > self.application_deadline:
            return False
        return True
    
    def can_trigger_shortlisting(self):
        """Check if shortlisting can be triggered (deadline passed or manual trigger)."""
        return timezone.now() > self.application_deadline or self.status == 'CLOSED'
