"""
Job management models for POSB Recruitment Portal.
Skills and D365-aligned job adverts.
"""
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


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


class EducationLevel(models.Model):
    """Education levels that must match D365 HcmEducationLevel values."""
    name = models.CharField(max_length=255, unique=True, help_text='Must match D365 HcmEducationLevel description')
    d365_code = models.CharField(max_length=50, blank=True, help_text='D365 education level ID/code')
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'education_levels'
        verbose_name = 'Education Level'
        verbose_name_plural = 'Education Levels'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class Country(models.Model):
    """
    Country reference data with ISO codes for D365 integration.
    D365 expects Country as ISO-2 (e.g. ZW) and Citizenship as ISO-3 (e.g. ZWE).
    """
    name = models.CharField(max_length=255, unique=True)
    iso2 = models.CharField(max_length=2, unique=True, help_text='ISO 3166-1 alpha-2 (e.g. ZW)')
    iso3 = models.CharField(max_length=3, unique=True, help_text='ISO 3166-1 alpha-3 (e.g. ZWE)')
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0, help_text='Lower = higher in dropdown. Use 0 for commonly used countries.')

    class Meta:
        db_table = 'countries'
        verbose_name = 'Country'
        verbose_name_plural = 'Countries'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return f'{self.name} ({self.iso2})'


class JobAdvert(models.Model):
    """
    Job advertisement model aligned with D365 vacancy payload.
    """
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
    ]

    recruiting_id = models.CharField(max_length=255, unique=True)
    job_id = models.CharField(max_length=255)
    job_title = models.CharField(max_length=255)
    job_description = models.TextField(max_length=4000)
    skills = models.TextField(blank=True, max_length=4000)
    certificates = models.TextField(blank=True, max_length=4000)
    education = models.TextField(blank=True, max_length=4000)
    job_tasks = models.TextField(blank=True, max_length=4000)
    responsibilities = models.TextField(blank=True, max_length=4000)
    years_of_experience = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(50)]
    )
    location = models.CharField(max_length=255, blank=True)
    job_type = models.CharField(max_length=255, blank=True)
    job_function = models.CharField(max_length=255, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='OPEN',
        help_text='Current status of the job advert'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'job_adverts'
        verbose_name = 'Job Advert'
        verbose_name_plural = 'Job Adverts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'end_date']),
            models.Index(fields=['job_function']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f'{self.job_title} - {self.job_id}'

    def is_open_for_applications(self):
        """Check if job is open and accepting applications."""
        if self.status != 'OPEN':
            return False
        if self.end_date and timezone.now() > self.end_date:
            return False
        return True

    def can_trigger_shortlisting(self):
        """Check if shortlisting can be triggered (deadline passed or manual trigger)."""
        if self.status == 'CLOSED':
            return True
        if self.end_date and timezone.now() > self.end_date:
            return True
        return False

    def get_skills_list(self):
        """Return skills as a list."""
        if not self.skills:
            return []
        return [s.strip() for s in self.skills.split(';') if s.strip()]

    def get_certificates_list(self):
        """Return certificates as a list."""
        if not self.certificates:
            return []
        return [c.strip() for c in self.certificates.split(';') if c.strip()]

    def get_education_list(self):
        """Return education as a list."""
        if not self.education:
            return []
        return [e.strip() for e in self.education.split(';') if e.strip()]

    def get_job_tasks_list(self):
        """Return job tasks as a list."""
        if not self.job_tasks:
            return []
        return [t.strip() for t in self.job_tasks.split(';') if t.strip()]

    def get_responsibilities_list(self):
        """Return responsibilities as a list."""
        if not self.responsibilities:
            return []
        return [r.strip() for r in self.responsibilities.split(';') if r.strip()]
