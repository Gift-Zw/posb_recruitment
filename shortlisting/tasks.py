"""
Shortlisting tasks (synchronous - Celery removed).
These functions run synchronously. To re-enable async processing, convert back to Celery tasks.
"""
from .services import AIShortlistingService
from system_logs.services import log_system_event


def trigger_shortlisting_task(job_advert_id, triggered_by_id=None, trigger_type='AUTOMATIC'):
    """
    Trigger AI shortlisting (synchronous).
    
    Args:
        job_advert_id: ID of the job advert
        triggered_by_id: User ID who triggered (None for automatic)
        trigger_type: 'AUTOMATIC' or 'MANUAL'
    """
    try:
        from accounts.models import User
        triggered_by = User.objects.get(id=triggered_by_id) if triggered_by_id else None
        
        AIShortlistingService.shortlist_candidates(
            job_advert_id=job_advert_id,
            triggered_by=triggered_by,
            trigger_type=trigger_type
        )
    except Exception as e:
        log_system_event(
            level='ERROR',
            source='SYSTEM',
            message=f'Failed to trigger shortlisting: {str(e)}',
            module='shortlisting.tasks',
            function='trigger_shortlisting_task'
        )
        raise


def check_deadline_and_shortlist():
    """
    Periodic task to check for job adverts past deadline and trigger shortlisting.
    Note: This function is no longer automatically scheduled. 
    Call it manually or set up a cron job to run it periodically.
    """
    from django.utils import timezone
    from jobs.models import JobAdvert
    
    # Find job adverts past deadline that haven't been shortlisted
    past_deadline_jobs = JobAdvert.objects.filter(
        status='OPEN',
        application_deadline__lt=timezone.now()
    )
    
    for job in past_deadline_jobs:
        # Check if shortlisting already in progress or completed
        from shortlisting.models import ShortlistingRun
        existing_run = ShortlistingRun.objects.filter(
            job_advert=job,
            status__in=['PENDING', 'IN_PROGRESS']
        ).exists()
        
        if not existing_run:
            trigger_shortlisting_task(job.id, triggered_by_id=None, trigger_type='AUTOMATIC')
