"""
Email notification tasks (synchronous - Celery removed).
These functions run synchronously. To re-enable async processing, convert back to Celery tasks.
"""
import threading
from .services import EmailService
from accounts.models import OTP
from applications.models import Application
from system_logs.services import log_system_event


def send_otp_email_task(otp_id):
    """Send OTP email (synchronous)."""
    try:
        otp = OTP.objects.get(id=otp_id)
        EmailService.send_otp_email(otp)
    except OTP.DoesNotExist:
        log_system_event(
            level='ERROR',
            source='SYSTEM',
            message=f'OTP not found: {otp_id}',
            module='notifications.tasks',
            function='send_otp_email_task'
        )
    except (TimeoutError, ConnectionError, OSError) as e:
        # Network errors - log but don't break flow
        log_system_event(
            level='ERROR',
            source='SYSTEM',
            message=f'Network error sending OTP email: {str(e)}',
            module='notifications.tasks',
            function='send_otp_email_task'
        )
        # Don't raise - OTP is generated, email failure shouldn't block user
    except Exception as e:
        log_system_event(
            level='ERROR',
            source='SYSTEM',
            message=f'Failed to send OTP email: {str(e)}',
            module='notifications.tasks',
            function='send_otp_email_task'
        )
        # Don't raise - OTP is generated, email failure shouldn't block user


def send_application_submitted_email_task(application_id):
    """Send application submitted email (synchronous)."""
    try:
        application = Application.objects.get(id=application_id)
        EmailService.send_application_submitted_email(application)
    except Application.DoesNotExist:
        log_system_event(
            level='ERROR',
            source='SYSTEM',
            message=f'Application not found: {application_id}',
            module='notifications.tasks',
            function='send_application_submitted_email_task'
        )
    except (TimeoutError, ConnectionError, OSError) as e:
        # Network errors - log but don't break flow
        log_system_event(
            level='ERROR',
            source='SYSTEM',
            message=f'Network error sending application submitted email: {str(e)}',
            module='notifications.tasks',
            function='send_application_submitted_email_task'
        )
        # Don't raise - application is saved, email failure shouldn't block


def enqueue_send_application_submitted_email_task(application_id):
    """Fire-and-forget wrapper for application submitted email."""
    try:
        worker = threading.Thread(
            target=send_application_submitted_email_task,
            args=(application_id,),
            daemon=True,
            name=f"email-application-submitted-{application_id}",
        )
        worker.start()
        return True
    except Exception as e:
        log_system_event(
            level='ERROR',
            source='SYSTEM',
            message=f'Failed to enqueue application submitted email: {str(e)}',
            module='notifications.tasks',
            function='enqueue_send_application_submitted_email_task'
        )
        return False
    except Exception as e:
        log_system_event(
            level='ERROR',
            source='SYSTEM',
            message=f'Failed to send application submitted email: {str(e)}',
            module='notifications.tasks',
            function='send_application_submitted_email_task'
        )
        # Don't raise - application is saved, email failure shouldn't block


def send_shortlisted_email_task(application_id):
    """Send shortlisted email (synchronous)."""
    try:
        application = Application.objects.get(id=application_id)
        EmailService.send_shortlisted_email(application)
    except Application.DoesNotExist:
        log_system_event(
            level='ERROR',
            source='SYSTEM',
            message=f'Application not found: {application_id}',
            module='notifications.tasks',
            function='send_shortlisted_email_task'
        )
    except (TimeoutError, ConnectionError, OSError) as e:
        # Network errors - log but don't break flow
        log_system_event(
            level='ERROR',
            source='SYSTEM',
            message=f'Network error sending shortlisted email: {str(e)}',
            module='notifications.tasks',
            function='send_shortlisted_email_task'
        )
        # Don't raise - shortlisting is processed, email failure shouldn't block
    except Exception as e:
        log_system_event(
            level='ERROR',
            source='SYSTEM',
            message=f'Failed to send shortlisted email: {str(e)}',
            module='notifications.tasks',
            function='send_shortlisted_email_task'
        )
        # Don't raise - shortlisting is processed, email failure shouldn't block


def send_rejected_email_task(application_id):
    """Send rejected email (synchronous)."""
    try:
        application = Application.objects.get(id=application_id)
        EmailService.send_rejected_email(application)
    except Application.DoesNotExist:
        log_system_event(
            level='ERROR',
            source='SYSTEM',
            message=f'Application not found: {application_id}',
            module='notifications.tasks',
            function='send_rejected_email_task'
        )
    except (TimeoutError, ConnectionError, OSError) as e:
        # Network errors - log but don't break flow
        log_system_event(
            level='ERROR',
            source='SYSTEM',
            message=f'Network error sending rejected email: {str(e)}',
            module='notifications.tasks',
            function='send_rejected_email_task'
        )
        # Don't raise - rejection is processed, email failure shouldn't block
    except Exception as e:
        log_system_event(
            level='ERROR',
            source='SYSTEM',
            message=f'Failed to send rejected email: {str(e)}',
            module='notifications.tasks',
            function='send_rejected_email_task'
        )
        # Don't raise - rejection is processed, email failure shouldn't block
