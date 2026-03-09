"""
Account models for POSB Recruitment Portal.
Custom User model and OTP verification system.
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.core.validators import EmailValidator
import secrets
import string


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user with email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser with email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)
        # Superusers are employees by default (can be changed in admin)
        extra_fields.setdefault('user_type', 'EMPLOYEE')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model with email as username.
    Users are inactive until OTP verification is complete.
    """
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator()],
        help_text='Email address used for login'
    )
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    
    # Status flags
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(
        default=False,
        help_text='Designates whether this user has verified their email via OTP.'
    )
    force_password_reset = models.BooleanField(
        default=False,
        help_text='Require user to change password before accessing the portal.'
    )
    
    # Timestamps
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # User type: 'APPLICANT' or 'EMPLOYEE'
    USER_TYPE_CHOICES = [
        ('APPLICANT', 'Applicant'),
        ('EMPLOYEE', 'Employee'),
    ]
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='APPLICANT',
        help_text='Type of user: Applicant (self-registered) or Employee (created by admin)'
    )
    
    # Legacy field for backward compatibility (deprecated - use user_type instead)
    is_hr_staff = models.BooleanField(
        default=False,
        help_text='DEPRECATED: Use user_type instead. Designates whether this user is POSB HR staff.'
    )
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_verified', 'is_active']),
        ]
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Return the full name of the user."""
        return f'{self.first_name} {self.last_name}'.strip() or self.email
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name or self.email
    
    def is_applicant(self):
        """Check if user is an applicant."""
        # Superusers are not applicants
        if self.is_superuser:
            return False
        return self.user_type == 'APPLICANT'
    
    def is_employee(self):
        """Check if user is an employee."""
        # Superusers are always considered employees for management portal access
        if self.is_superuser:
            return True
        return self.user_type == 'EMPLOYEE'


class OTP(models.Model):
    """
    One-Time Password model for email verification.
    Supports configurable expiry and max attempts.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='otps',
        help_text='User requesting OTP verification'
    )
    code = models.CharField(
        max_length=10,
        help_text='OTP code sent to user'
    )
    purpose = models.CharField(
        max_length=50,
        default='email_verification',
        help_text='Purpose of OTP (email_verification, password_reset, etc.)'
    )
    
    # Expiry and attempts
    expires_at = models.DateTimeField(
        help_text='Timestamp when OTP expires'
    )
    attempts = models.IntegerField(
        default=0,
        help_text='Number of verification attempts made'
    )
    max_attempts = models.IntegerField(
        default=3,
        help_text='Maximum allowed verification attempts'
    )
    
    # Status
    is_used = models.BooleanField(
        default=False,
        help_text='Whether this OTP has been successfully used'
    )
    is_expired = models.BooleanField(
        default=False,
        help_text='Whether this OTP has expired'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'otps'
        verbose_name = 'OTP'
        verbose_name_plural = 'OTPs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'purpose', 'is_used', 'is_expired']),
            models.Index(fields=['code']),
        ]
    
    def __str__(self):
        return f'OTP for {self.user.email} - {self.purpose}'
    
    def is_valid(self):
        """Check if OTP is still valid (not used, not expired, within attempts)."""
        if self.is_used:
            return False
        if self.is_expired:
            return False
        if self.attempts >= self.max_attempts:
            return False
        if timezone.now() > self.expires_at:
            self.is_expired = True
            self.save(update_fields=['is_expired'])
            return False
        return True
    
    def mark_as_used(self):
        """Mark OTP as used."""
        self.is_used = True
        self.used_at = timezone.now()
        self.save(update_fields=['is_used', 'used_at'])
    
    def increment_attempts(self):
        """Increment verification attempts."""
        self.attempts += 1
        self.save(update_fields=['attempts'])
    
    @staticmethod
    def generate_code(length=6):
        """Generate a random numeric OTP code."""
        return ''.join(secrets.choice(string.digits) for _ in range(length))


class EmployeeProfile(models.Model):
    """
    Employee profile model for POSB staff.
    Minimal profile with only EC number and phone number.
    Linked directly to User model where user_type='EMPLOYEE'.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='employee_profile',
        limit_choices_to={'user_type': 'EMPLOYEE'},
        help_text='User account (must be employee type)'
    )
    
    # Employee Information
    ec_number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        help_text='Employee Code (EC) Number'
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        help_text='Phone number'
    )
    department = models.CharField(
        max_length=200,
        blank=True,
        help_text='Department/Division'
    )
    job_title = models.CharField(
        max_length=200,
        blank=True,
        help_text='Job title/position'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'employee_profiles'
        verbose_name = 'Employee Profile'
        verbose_name_plural = 'Employee Profiles'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['ec_number']),
        ]
    
    def __str__(self):
        return f'Profile for {self.user.get_full_name()} ({self.ec_number})'
