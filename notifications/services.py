"""
Email notification service for POSB Recruitment Portal.
"""
import threading
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from .models import EmailNotification
from audit.services import log_audit_event
from system_logs.services import log_system_event


class EmailService:
    """Service for sending email notifications."""
    
    @staticmethod
    def send_otp_email(otp):
        """Send OTP verification email."""
        try:
            notification = EmailNotification.objects.create(
                recipient=otp.user,
                notification_type='OTP_VERIFICATION',
                subject='Verify Your Email - POSB Recruitment Portal',
                message=f'Your OTP code is: {otp.code}. This code expires in {settings.OTP_EXPIRY_MINUTES} minutes.',
                related_otp=otp,
                metadata={'otp_id': otp.id, 'purpose': otp.purpose}
            )
            
            # Render HTML email template
            html_message = render_to_string('notifications/emails/otp_verification.html', {
                'otp': otp,
                'otp_expiry_minutes': settings.OTP_EXPIRY_MINUTES,
            })
            
            # Send email in background thread to avoid blocking the request
            def send_email_thread():
                try:
                    send_mail(
                        subject=notification.subject,
                        message=notification.message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[otp.user.email],
                        html_message=html_message,
                        fail_silently=False
                    )
                    notification.mark_as_sent()
                    
                    # Audit log
                    log_audit_event(
                        actor=otp.user,
                        action='EMAIL_SENT',
                        action_description=f'OTP email sent to {otp.user.email}',
                        entity=notification,
                        metadata={'notification_type': 'OTP_VERIFICATION'}
                    )
                except (TimeoutError, ConnectionError, OSError) as e:
                    # Network-related errors - log but don't break flow
                    notification.mark_as_failed(str(e))
                    log_system_event(
                        level='ERROR',
                        source='SYSTEM',
                        message=f'Network error sending OTP email: {str(e)}',
                        module='notifications.services',
                        function='send_otp_email',
                        related_user=otp.user
                    )
                except Exception as e:
                    # Other email errors
                    notification.mark_as_failed(str(e))
                    log_system_event(
                        level='ERROR',
                        source='SYSTEM',
                        message=f'Failed to send OTP email: {str(e)}',
                        module='notifications.services',
                        function='send_otp_email',
                        related_user=otp.user
                    )
            
            # Start email sending in background thread (non-daemon so it completes)
            thread = threading.Thread(target=send_email_thread)
            thread.start()
            # Don't wait for thread - let it run in background
            
            return notification
            
        except Exception as e:
            if 'notification' in locals():
                notification.mark_as_failed(str(e))
            log_system_event(
                level='ERROR',
                source='SYSTEM',
                message=f'Failed to create OTP email notification: {str(e)}',
                module='notifications.services',
                function='send_otp_email'
            )
            # Don't raise - OTP is already generated, email failure shouldn't block user
    
    @staticmethod
    def send_application_submitted_email(application):
        """Send application submission confirmation email."""
        try:
            notification = EmailNotification.objects.create(
                recipient=application.applicant,
                notification_type='APPLICATION_SUBMITTED',
                subject=f'Application Submitted - {application.job_advert.job_title}',
                message=f'Your application for {application.job_advert.job_title} has been successfully submitted.',
                related_application=application,
                metadata={'application_id': application.id, 'job_title': application.job_advert.job_title}
            )
            
            # Build portal URL
            portal_url = f"{settings.SITE_URL or 'http://localhost:8000'}{reverse('applications:list')}"
            
            # Render HTML email template
            html_message = render_to_string('notifications/emails/application_submitted.html', {
                'application': application,
                'portal_url': portal_url,
            })
            
            # Send email synchronously
            try:
                send_mail(
                    subject=notification.subject,
                    message=notification.message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[application.applicant.email],
                    html_message=html_message,
                    fail_silently=False
                )
                notification.mark_as_sent()
                
                log_audit_event(
                    actor=application.applicant,
                    action='EMAIL_SENT',
                    action_description=f'Application submitted email sent to {application.applicant.email}',
                    entity=notification
                )
            except (TimeoutError, ConnectionError, OSError) as e:
                # Network-related errors - log but don't break flow
                notification.mark_as_failed(str(e))
                log_system_event(
                    level='ERROR',
                    source='SYSTEM',
                    message=f'Network error sending application submitted email: {str(e)}',
                    module='notifications.services',
                    function='send_application_submitted_email',
                    related_user=application.applicant
                )
                # Don't raise - allow application to be saved even if email fails
            except Exception as e:
                # Other email errors - log but don't break flow for non-critical emails
                notification.mark_as_failed(str(e))
                log_system_event(
                    level='ERROR',
                    source='SYSTEM',
                    message=f'Failed to send application submitted email: {str(e)}',
                    module='notifications.services',
                    function='send_application_submitted_email',
                    related_user=application.applicant
                )
                # Don't raise - allow application to be saved even if email fails
            
            return notification
            
        except Exception as e:
            if 'notification' in locals():
                notification.mark_as_failed(str(e))
            log_system_event(
                level='ERROR',
                source='SYSTEM',
                message=f'Failed to create application submitted email notification: {str(e)}',
                module='notifications.services',
                function='send_application_submitted_email'
            )
            # Don't raise - application is already saved, notification failure shouldn't block
    
    @staticmethod
    def send_shortlisted_email(application):
        """Send shortlisted notification email."""
        try:
            notification = EmailNotification.objects.create(
                recipient=application.applicant,
                notification_type='SHORTLISTED',
                subject=f'Congratulations! You have been shortlisted - {application.job_advert.job_title}',
                message=f'Congratulations! Your application for {application.job_advert.job_title} has been shortlisted. We will contact you soon.',
                related_application=application,
                metadata={'application_id': application.id}
            )
            
            # Build portal URL
            portal_url = f"{settings.SITE_URL or 'http://localhost:8000'}{reverse('applications:list')}"
            
            # Render HTML email template
            html_message = render_to_string('notifications/emails/shortlisted.html', {
                'application': application,
                'portal_url': portal_url,
            })
            
            # Send email synchronously
            try:
                send_mail(
                    subject=notification.subject,
                    message=notification.message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[application.applicant.email],
                    html_message=html_message,
                    fail_silently=False
                )
                notification.mark_as_sent()
                
                log_audit_event(
                    actor=application.applicant,
                    action='EMAIL_SENT',
                    action_description=f'Shortlisted email sent to {application.applicant.email}',
                    entity=notification
                )
            except (TimeoutError, ConnectionError, OSError) as e:
                # Network-related errors - log but don't break flow
                notification.mark_as_failed(str(e))
                log_system_event(
                    level='ERROR',
                    source='SYSTEM',
                    message=f'Network error sending shortlisted email: {str(e)}',
                    module='notifications.services',
                    function='send_shortlisted_email',
                    related_user=application.applicant
                )
                # Don't raise - allow shortlisting to complete even if email fails
            except Exception as e:
                # Other email errors - log but don't break flow
                notification.mark_as_failed(str(e))
                log_system_event(
                    level='ERROR',
                    source='SYSTEM',
                    message=f'Failed to send shortlisted email: {str(e)}',
                    module='notifications.services',
                    function='send_shortlisted_email',
                    related_user=application.applicant
                )
                # Don't raise - allow shortlisting to complete even if email fails
            
            return notification
            
        except Exception as e:
            if 'notification' in locals():
                notification.mark_as_failed(str(e))
            log_system_event(
                level='ERROR',
                source='SYSTEM',
                message=f'Failed to create shortlisted email notification: {str(e)}',
                module='notifications.services',
                function='send_shortlisted_email'
            )
            # Don't raise - shortlisting is already processed, notification failure shouldn't block
    
    @staticmethod
    def send_rejected_email(application):
        """Send rejection notification email."""
        try:
            notification = EmailNotification.objects.create(
                recipient=application.applicant,
                notification_type='REJECTED',
                subject=f'Application Update - {application.job_advert.job_title}',
                message=f'Thank you for your interest. Unfortunately, your application for {application.job_advert.job_title} was not successful at this time.',
                related_application=application,
                metadata={'application_id': application.id}
            )
            
            # Build portal URL
            portal_url = f"{settings.SITE_URL or 'http://localhost:8000'}{reverse('jobs:list')}"
            
            # Render HTML email template
            html_message = render_to_string('notifications/emails/rejected.html', {
                'application': application,
                'portal_url': portal_url,
            })
            
            # Send email synchronously
            try:
                send_mail(
                    subject=notification.subject,
                    message=notification.message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[application.applicant.email],
                    html_message=html_message,
                    fail_silently=False
                )
                notification.mark_as_sent()
                
                log_audit_event(
                    actor=application.applicant,
                    action='EMAIL_SENT',
                    action_description=f'Rejection email sent to {application.applicant.email}',
                    entity=notification
                )
            except (TimeoutError, ConnectionError, OSError) as e:
                # Network-related errors - log but don't break flow
                notification.mark_as_failed(str(e))
                log_system_event(
                    level='ERROR',
                    source='SYSTEM',
                    message=f'Network error sending rejected email: {str(e)}',
                    module='notifications.services',
                    function='send_rejected_email',
                    related_user=application.applicant
                )
                # Don't raise - allow rejection to be processed even if email fails
            except Exception as e:
                # Other email errors - log but don't break flow
                notification.mark_as_failed(str(e))
                log_system_event(
                    level='ERROR',
                    source='SYSTEM',
                    message=f'Failed to send rejected email: {str(e)}',
                    module='notifications.services',
                    function='send_rejected_email',
                    related_user=application.applicant
                )
                # Don't raise - allow rejection to be processed even if email fails
            
            return notification
            
        except Exception as e:
            if 'notification' in locals():
                notification.mark_as_failed(str(e))
            log_system_event(
                level='ERROR',
                source='SYSTEM',
                message=f'Failed to create rejected email notification: {str(e)}',
                module='notifications.services',
                function='send_rejected_email'
            )
            # Don't raise - rejection is already processed, notification failure shouldn't block
