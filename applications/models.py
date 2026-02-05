"""
Application models for POSB Recruitment Portal.
Applicant profiles, applications, and document uploads.
"""
from django.db import models
from django.utils import timezone
from django.core.validators import FileExtensionValidator


class ApplicantProfile(models.Model):
    """
    Detailed applicant profile model.
    Stores comprehensive personal, education, experience, and skills information.
    Only for users with user_type='APPLICANT' (not employees).
    """
    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='applicant_profile',
        limit_choices_to={'user_type': 'APPLICANT'}
    )
    
    # Contact Information
    phone_number = models.CharField(max_length=20, blank=True)
    alternate_phone = models.CharField(max_length=20, blank=True, help_text='Alternate contact number')
    email = models.EmailField(blank=True, help_text='Primary email (if different from user email)')
    
    # Personal Information
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=20,
        choices=[
            ('MALE', 'Male'),
            ('FEMALE', 'Female'),
            ('OTHER', 'Other'),
            ('PREFER_NOT_TO_SAY', 'Prefer not to say'),
        ],
        blank=True
    )
    nationality = models.CharField(max_length=100, blank=True)
    id_number = models.CharField(max_length=50, blank=True, help_text='National ID / Passport Number')
    marital_status = models.CharField(
        max_length=20,
        choices=[
            ('SINGLE', 'Single'),
            ('MARRIED', 'Married'),
            ('DIVORCED', 'Divorced'),
            ('WIDOWED', 'Widowed'),
        ],
        blank=True
    )
    
    # Address Information
    address_line_1 = models.CharField(max_length=255, blank=True, help_text='Street address')
    address_line_2 = models.CharField(max_length=255, blank=True, help_text='Apartment, suite, etc.')
    city = models.CharField(max_length=100, blank=True)
    state_province = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True, default='Singapore')
    
    # Education (detailed JSON)
    education = models.JSONField(
        default=list,
        help_text='List of education: [{"institution": "...", "degree": "...", "field": "...", "start_year": "...", "end_year": "...", "gpa": "...", "honors": "..."}]'
    )
    
    # Work Experience (detailed JSON)
    experience = models.JSONField(
        default=list,
        help_text='List of work experience: [{"company": "...", "position": "...", "start_date": "...", "end_date": "...", "current": false, "responsibilities": "...", "achievements": "..."}]'
    )
    
    # Skills
    skills = models.ManyToManyField(
        'jobs.Skill',
        related_name='applicant_profiles',
        blank=True
    )
    languages = models.JSONField(
        default=list,
        help_text='Languages: [{"language": "...", "proficiency": "Native/Fluent/Intermediate/Basic"}]'
    )
    certifications = models.JSONField(
        default=list,
        help_text='Certifications: [{"name": "...", "issuing_organization": "...", "issue_date": "...", "expiry_date": "...", "credential_id": "..."}]'
    )
    
    # References
    references = models.JSONField(
        default=list,
        help_text='References: [{"name": "...", "position": "...", "company": "...", "email": "...", "phone": "..."}]'
    )
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True, help_text='Relationship to applicant')
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_email = models.EmailField(blank=True)
    
    # Additional Information
    professional_summary = models.TextField(blank=True, help_text='Professional summary / About yourself')
    cover_letter = models.TextField(blank=True, help_text='Cover letter / Personal statement')
    
    # Social Media & Online Presence
    linkedin_url = models.URLField(blank=True, help_text='LinkedIn profile URL')
    github_url = models.URLField(blank=True, help_text='GitHub profile URL')
    twitter_url = models.URLField(blank=True, help_text='Twitter/X profile URL')
    facebook_url = models.URLField(blank=True, help_text='Facebook profile URL')
    instagram_url = models.URLField(blank=True, help_text='Instagram profile URL')
    youtube_url = models.URLField(blank=True, help_text='YouTube channel URL')
    behance_url = models.URLField(blank=True, help_text='Behance portfolio URL')
    dribbble_url = models.URLField(blank=True, help_text='Dribbble portfolio URL')
    medium_url = models.URLField(blank=True, help_text='Medium profile URL')
    stackoverflow_url = models.URLField(blank=True, help_text='Stack Overflow profile URL')
    portfolio_url = models.URLField(blank=True, help_text='Portfolio / Personal website URL')
    
    # Projects (detailed JSON)
    projects = models.JSONField(
        default=list,
        blank=True,
        help_text='List of projects: [{"name": "...", "description": "...", "technologies": "...", "url": "...", "start_date": "...", "end_date": "...", "current": false}]'
    )
    
    availability_date = models.DateField(null=True, blank=True, help_text='Earliest available start date')
    current_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Current salary (if applicable)')
    expected_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Expected salary range')
    notice_period = models.CharField(max_length=50, blank=True, help_text='Notice period (e.g., "2 weeks", "1 month")')
    additional_info = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional flexible information as JSON'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'applicant_profiles'
        verbose_name = 'Applicant Profile'
        verbose_name_plural = 'Applicant Profiles'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['city', 'country']),
        ]
    
    def __str__(self):
        return f'Profile for {self.user.email}'
    
    @property
    def completion_percentage(self):
        """Calculate profile completion percentage based on filled fields."""
        total_fields = 0
        filled_fields = 0
        
        # Personal Information (8 fields)
        personal_fields = [
            self.user.first_name, self.user.last_name,
            self.phone_number, self.date_of_birth, self.gender,
            self.nationality, self.id_number, self.marital_status
        ]
        total_fields += 8
        filled_fields += sum(1 for field in personal_fields if field)
        
        # Address Information (5 fields)
        address_fields = [
            self.address_line_1, self.city, self.state_province,
            self.postal_code, self.country
        ]
        total_fields += 5
        filled_fields += sum(1 for field in address_fields if field)
        
        # Education (at least 1 entry)
        total_fields += 1
        if self.education and len(self.education) > 0:
            filled_fields += 1
        
        # Work Experience (at least 1 entry)
        total_fields += 1
        if self.experience and len(self.experience) > 0:
            filled_fields += 1
        
        # Skills (at least 1 skill)
        total_fields += 1
        if self.skills.exists():
            filled_fields += 1
        
        # Languages (at least 1 entry)
        total_fields += 1
        if self.languages and len(self.languages) > 0:
            filled_fields += 1
        
        # Cover Letter
        total_fields += 1
        if self.cover_letter:
            filled_fields += 1
        
        # Calculate percentage
        if total_fields == 0:
            return 0
        return int((filled_fields / total_fields) * 100)


class ApplicantProfileDocument(models.Model):
    """Documents uploaded to applicant profile (can be reused across applications)."""
    DOCUMENT_TYPE_CHOICES = [
        ('CV', 'Curriculum Vitae / Resume'),
        ('BACHELORS_DEGREE', "Bachelor's Degree Certificate"),
        ('MASTERS_DEGREE', "Master's Degree Certificate"),
        ('DOCTORATE_DEGREE', 'Doctorate Degree Certificate'),
        ('DIPLOMA', 'Diploma Certificate'),
        ('TRANSCRIPT', 'Academic Transcript'),
        ('CERTIFICATE', 'Professional Certificate'),
        ('COVER_LETTER', 'Cover Letter'),
        ('ID_COPY', 'ID Copy / Passport'),
        ('REFERENCE_LETTER', 'Reference Letter'),
        ('PORTFOLIO', 'Portfolio'),
        ('OTHER', 'Other'),
    ]
    
    applicant_profile = models.ForeignKey(
        'ApplicantProfile',
        on_delete=models.CASCADE,
        related_name='documents'
    )
    document_type = models.CharField(
        max_length=50,
        choices=DOCUMENT_TYPE_CHOICES,
        default='CV'
    )
    file = models.FileField(
        upload_to='applicant_documents/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])]
    )
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField(help_text='File size in bytes')
    description = models.CharField(max_length=255, blank=True, help_text='Optional description')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'applicant_profile_documents'
        verbose_name = 'Applicant Profile Document'
        verbose_name_plural = 'Applicant Profile Documents'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['applicant_profile', 'document_type']),
        ]
    
    def __str__(self):
        return f'{self.document_type} - {self.file_name}'
    
    def get_file_size_display(self):
        """Return human-readable file size."""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


class ApplicationDocument(models.Model):
    """Document uploads for applications (CV, certificates, etc.)."""
    application = models.ForeignKey(
        'Application',
        on_delete=models.CASCADE,
        related_name='documents'
    )
    document_type = models.CharField(
        max_length=50,
        choices=[
            ('CV', 'Curriculum Vitae'),
            ('CERTIFICATE', 'Certificate'),
            ('TRANSCRIPT', 'Transcript'),
            ('COVER_LETTER', 'Cover Letter'),
            ('OTHER', 'Other'),
        ],
        default='CV'
    )
    file = models.FileField(
        upload_to='application_documents/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])]
    )
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField(help_text='File size in bytes')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'application_documents'
        verbose_name = 'Application Document'
        verbose_name_plural = 'Application Documents'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['application', 'document_type']),
        ]
    
    def __str__(self):
        return f'{self.document_type} - {self.file_name}'


class ApplicationData(models.Model):
    """
    Immutable application data captured at submission time.
    Stores all applicant information as separate fields for better querying and data integrity.
    This ensures that profile changes don't affect submitted applications.
    """
    application = models.OneToOneField(
        'Application',
        on_delete=models.CASCADE,
        related_name='application_data'
    )
    
    # Contact Information
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    
    # Address (stored as single string for simplicity, matching original snapshot format)
    address = models.TextField(blank=True, help_text='Full address as submitted')
    
    # Personal Information
    date_of_birth = models.DateField(null=True, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    
    # Education and Experience (JSON arrays)
    education = models.JSONField(
        default=list,
        help_text='List of education: [{"institution": "...", "degree": "...", "field": "...", "start_year": "...", "end_year": "...", "gpa": "...", "honors": "..."}]'
    )
    experience = models.JSONField(
        default=list,
        help_text='List of work experience: [{"company": "...", "position": "...", "start_date": "...", "end_date": "...", "current": false, "responsibilities": "...", "achievements": "..."}]'
    )
    
    # Skills (stored as semicolon-separated text)
    skills = models.TextField(
        blank=True,
        help_text='Skills separated by semicolons (;)'
    )
    
    # Cover Letter
    cover_letter = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'application_data'
        verbose_name = 'Application Data'
        verbose_name_plural = 'Application Data'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f'Application Data for {self.application}'
    
    def get_skills_list(self):
        """Return skills as a list."""
        if not self.skills:
            return []
        return [s.strip() for s in self.skills.split(';') if s.strip()]


class Application(models.Model):
    """
    Job application model.
    Links to ApplicationData which stores immutable snapshot of applicant profile at submission time.
    """
    STATUS_CHOICES = [
        ('SUBMITTED', 'Submitted'),
        ('UNDER_REVIEW', 'Under Review'),
        ('SHORTLISTED', 'Shortlisted'),
        ('REJECTED', 'Rejected'),
    ]
    
    applicant = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='applications'
    )
    job_advert = models.ForeignKey(
        'jobs.JobAdvert',
        on_delete=models.CASCADE,
        related_name='applications'
    )
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='SUBMITTED'
    )
    
    # AI Shortlisting
    ai_score = models.FloatField(
        null=True,
        blank=True,
        help_text='AI-generated score (0-100) for shortlisting'
    )
    ai_ranking = models.IntegerField(
        null=True,
        blank=True,
        help_text='Ranking position after AI shortlisting'
    )
    ai_explanation = models.TextField(
        blank=True,
        help_text='AI explanation for the score/ranking'
    )
    ai_shortlisted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when AI shortlisting was performed'
    )
    
    # Timestamps
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'applications'
        verbose_name = 'Application'
        verbose_name_plural = 'Applications'
        ordering = ['-submitted_at']
        unique_together = [['applicant', 'job_advert']]
        indexes = [
            models.Index(fields=['applicant', 'status']),
            models.Index(fields=['job_advert', 'status']),
            models.Index(fields=['status', 'ai_ranking']),
            models.Index(fields=['submitted_at']),
        ]
    
    def __str__(self):
        return f'{self.applicant.email} - {self.job_advert.job_title}'
    
    def get_last_application_data(self):
        """
        Get ApplicationData from the last submitted application for reuse.
        Returns None if no previous application exists.
        """
        last_application = Application.objects.filter(
            applicant=self.applicant
        ).exclude(
            id=self.id
        ).order_by('-submitted_at').first()
        
        if last_application and hasattr(last_application, 'application_data'):
            return last_application.application_data
        return None
