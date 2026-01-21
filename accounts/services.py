"""
Business logic services for accounts app.
OTP generation, verification, and user management.
"""
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
from .models import User, OTP
from notifications.tasks import send_otp_email_task
from audit.services import log_audit_event
from system_logs.services import log_system_event


class OTPService:
    """Service for OTP generation and verification."""
    
    @staticmethod
    def generate_otp(user, purpose='email_verification'):
        """
        Generate a new OTP for a user.
        Invalidates any existing unused OTPs for the same purpose.
        """
        # Invalidate existing unused OTPs for this purpose
        OTP.objects.filter(
            user=user,
            purpose=purpose,
            is_used=False,
            is_expired=False
        ).update(is_expired=True)
        
        # Generate new OTP
        code = OTP.generate_code(length=settings.OTP_LENGTH)
        expires_at = timezone.now() + timezone.timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
        
        otp = OTP.objects.create(
            user=user,
            code=code,
            purpose=purpose,
            expires_at=expires_at,
            max_attempts=settings.OTP_MAX_ATTEMPTS
        )
        
        # Send OTP via email (non-blocking - runs in background thread)
        send_otp_email_task(otp.id)
        
        # Audit log
        log_audit_event(
            actor=user,
            action='OTP_GENERATED',
            action_description=f'OTP generated for {purpose}',
            metadata={'purpose': purpose, 'otp_id': otp.id}
        )
        
        return otp
    
    @staticmethod
    def verify_otp(user, code, purpose='email_verification'):
        """
        Verify an OTP code for a user.
        Returns (success: bool, message: str, otp: OTP or None)
        """
        # Find valid OTP
        otp = OTP.objects.filter(
            user=user,
            purpose=purpose,
            is_used=False,
            is_expired=False
        ).order_by('-created_at').first()
        
        if not otp:
            log_audit_event(
                actor=user,
                action='OTP_VERIFICATION_FAILED',
                action_description=f'OTP verification failed: No valid OTP found',
                metadata={'purpose': purpose}
            )
            return False, 'No valid OTP found. Please request a new one.', None
        
        if not otp.is_valid():
            otp.increment_attempts()
            log_audit_event(
                actor=user,
                action='OTP_VERIFICATION_FAILED',
                action_description=f'OTP verification failed: Invalid or expired',
                metadata={'purpose': purpose, 'otp_id': otp.id}
            )
            return False, 'OTP is invalid or expired. Please request a new one.', None
        
        # Verify code
        if otp.code != code:
            otp.increment_attempts()
            log_audit_event(
                actor=user,
                action='OTP_VERIFICATION_FAILED',
                action_description=f'OTP verification failed: Incorrect code',
                metadata={'purpose': purpose, 'otp_id': otp.id}
            )
            return False, 'Incorrect OTP code. Please try again.', None
        
        # Success - mark as used
        otp.mark_as_used()
        
        # If email verification, activate user
        if purpose == 'email_verification':
            user.is_verified = True
            user.is_active = True
            user.save(update_fields=['is_verified', 'is_active'])
        
        # Audit log
        log_audit_event(
            actor=user,
            action='OTP_VERIFICATION',
            action_description=f'OTP verified successfully for {purpose}',
            metadata={'purpose': purpose, 'otp_id': otp.id}
        )
        
        return True, 'OTP verified successfully.', otp


class UserService:
    """Service for user management."""
    
    @staticmethod
    def register_user(email, password, first_name='', last_name=''):
        """
        Register a new user and send OTP for verification.
        Returns (user, otp, error_message)
        """
        try:
            # Check if user already exists
            if User.objects.filter(email=email).exists():
                return None, None, 'User with this email already exists.'
            
            # Create user (inactive until verified)
            # Only applicants can self-register
            # Set is_active=True so they can login, but is_verified=False so they must verify OTP
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                user_type='APPLICANT',  # Self-registration is only for applicants
                is_active=True,  # Active so they can login, but must verify OTP
                is_verified=False  # Must verify via OTP before full access
            )
            
            # Generate OTP
            otp = OTPService.generate_otp(user, purpose='email_verification')
            
            # Audit log
            log_audit_event(
                actor=user,
                action='USER_REGISTRATION',
                action_description=f'New user registered: {email}',
                metadata={'email': email}
            )
            
            return user, otp, None
            
        except Exception as e:
            log_system_event(
                level='ERROR',
                source='API',
                message=f'User registration failed: {str(e)}',
                module='accounts.services',
                function='register_user'
            )
            return None, None, f'Registration failed: {str(e)}'
