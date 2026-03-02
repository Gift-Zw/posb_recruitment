"""
Application models for POSB Recruitment Portal.
Applicant profiles, applications, and document uploads.
"""
from django.db import models
from django.utils import timezone
from django.core.validators import FileExtensionValidator


class ApplicantProfile(models.Model):
    """
    Applicant profile model aligned with D365 Applicant Import API fields.
    Only for users with user_type='APPLICANT'.
    """
    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='applicant_profile',
        limit_choices_to={'user_type': 'APPLICANT'}
    )
    
    # Contact Information
    phone_number = models.CharField(max_length=20, blank=True)
    alternate_phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True, help_text='Primary email (if different from user email)')
    
    # Personal Information (D365: FirstName/LastName on User model)
    middle_name = models.CharField(max_length=255, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=20,
        choices=[
            ('MALE', 'Male'),
            ('FEMALE', 'Female'),
        ],
        blank=True
    )
    citizenship = models.ForeignKey(
        'jobs.Country',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='citizens',
        help_text='Citizenship / Nationality — D365 sends ISO-3 (e.g. ZWE)'
    )
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
    
    # Address Information (D365: StreetAddress, City, ZipCode, Country)
    address_line_1 = models.CharField(max_length=255, blank=True, help_text='Street address')
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state_province = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.ForeignKey(
        'jobs.Country',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='residents',
        help_text='Country of residence — D365 sends ISO-2 (e.g. ZW)'
    )
    
    # Professional (D365: CurrentJobTitle, EducationLevelDescription)
    current_job_title = models.CharField(max_length=255, blank=True)
    education_level = models.ForeignKey(
        'jobs.EducationLevel',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='applicant_profiles',
        help_text='Highest education level (must match D365 HcmEducationLevel)'
    )
    
    # Education & Experience (detailed JSON for portal use)
    education = models.JSONField(default=list, blank=True)
    experience = models.JSONField(default=list, blank=True)
    
    # Skills
    skills = models.ManyToManyField(
        'jobs.Skill',
        related_name='applicant_profiles',
        blank=True
    )
    
    # Additional Information
    professional_summary = models.TextField(blank=True)
    cover_letter = models.TextField(blank=True)
    
    # Online Presence
    linkedin_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True, help_text='Portfolio / Personal website URL')
    
    availability_date = models.DateField(null=True, blank=True)
    current_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    expected_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notice_period = models.CharField(max_length=50, blank=True)
    
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
        total_fields = 0
        filled_fields = 0
        
        personal_fields = [
            self.user.first_name, self.user.last_name,
            self.phone_number, self.date_of_birth, self.gender,
            self.citizenship_id, self.id_number,
        ]
        total_fields += 7
        filled_fields += sum(1 for field in personal_fields if field)
        
        address_fields = [
            self.address_line_1, self.city, self.country_id
        ]
        total_fields += 3
        filled_fields += sum(1 for field in address_fields if field)
        
        total_fields += 1
        if self.education_level:
            filled_fields += 1
        
        total_fields += 1
        if self.skills.exists():
            filled_fields += 1
        
        total_fields += 1
        if self.cover_letter:
            filled_fields += 1
        
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
    Fields are aligned with the D365 Applicant Import API contract.
    This ensures that profile changes don't affect submitted applications.
    """
    application = models.OneToOneField(
        'Application',
        on_delete=models.CASCADE,
        related_name='application_data'
    )
    
    # D365 contract fields (PascalCase mapping in comments)
    first_name = models.CharField(max_length=255)  # FirstName
    last_name = models.CharField(max_length=255)  # LastName
    middle_name = models.CharField(max_length=255, blank=True)  # MiddleName
    email = models.EmailField()  # Email
    phone_number = models.CharField(max_length=20, blank=True)  # Phone
    date_of_birth = models.DateField(null=True, blank=True)  # BirthDateUtc
    gender = models.CharField(max_length=20, blank=True)  # Gender (Male/Female)
    citizenship = models.CharField(max_length=10, blank=True, help_text='ISO-3 country code e.g. ZWE')  # Citizenship
    marital_status = models.CharField(max_length=20, blank=True)  # MaritalStatus
    street_address = models.CharField(max_length=255, blank=True)  # StreetAddress
    city = models.CharField(max_length=100, blank=True)  # City
    zip_code = models.CharField(max_length=20, blank=True)  # ZipCode
    country = models.CharField(max_length=10, blank=True, help_text='ISO-2 or ISO-3 country code')  # Country
    current_job_title = models.CharField(max_length=255, blank=True)  # CurrentJobTitle
    education_level = models.CharField(max_length=255, blank=True, help_text='Must match D365 HcmEducationLevel')  # EducationLevelDescription
    cover_letter = models.TextField(blank=True)  # CoverLetter

    # Extra fields (not in D365 contract but useful for portal)
    nationality = models.CharField(max_length=100, blank=True)
    education = models.JSONField(default=list, help_text='Detailed education entries')
    experience = models.JSONField(default=list, help_text='Detailed work experience entries')
    skills = models.TextField(blank=True, help_text='Skills separated by semicolons (;)')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'application_data'
        verbose_name = 'Application Data'
        verbose_name_plural = 'Application Data'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f'Application Data for {self.application}'
    
    def get_skills_list(self):
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

    D365_PUSH_STATUS_CHOICES = [
        ('NOT_PUSHED', 'Not Pushed'),
        ('PENDING', 'Pending'),
        ('PUSHED', 'Pushed'),
        ('DUPLICATE', 'Duplicate (Existing Applicant)'),
        ('FAILED', 'Failed'),
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

    # D365 Push tracking
    d365_push_status = models.CharField(
        max_length=20,
        choices=D365_PUSH_STATUS_CHOICES,
        default='NOT_PUSHED',
    )
    d365_applicant_id = models.CharField(
        max_length=50,
        blank=True,
        help_text='POSB-AI-XXXXX assigned by our system for D365'
    )
    d365_applicant_rec_id = models.BigIntegerField(
        null=True, blank=True,
        help_text='D365 HcmApplicant RecId'
    )
    d365_application_rec_id = models.BigIntegerField(
        null=True, blank=True,
        help_text='D365 HRMApplication RecId'
    )
    d365_push_error = models.TextField(
        blank=True,
        help_text='Error message from last D365 push attempt'
    )
    d365_pushed_at = models.DateTimeField(
        null=True, blank=True,
        help_text='When this application was pushed to D365'
    )
    d365_push_attempts = models.IntegerField(default=0)
    
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
