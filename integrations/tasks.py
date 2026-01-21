"""
ERP integration tasks (synchronous - Celery removed).
These functions run synchronously. To re-enable async processing, convert back to Celery tasks.
"""
from .services import Dynamics365Service
from system_logs.services import log_system_event


def export_to_erp_task(shortlisting_run_id, triggered_by_id=None):
    """
    Export shortlisted candidates to Dynamics 365 ERP (synchronous).
    
    Args:
        shortlisting_run_id: ID of the shortlisting run
        triggered_by_id: User ID who triggered the export
    """
    try:
        from accounts.models import User
        triggered_by = User.objects.get(id=triggered_by_id) if triggered_by_id else None
        
        Dynamics365Service.export_shortlisted_candidates(
            shortlisting_run_id=shortlisting_run_id,
            triggered_by=triggered_by
        )
    except Exception as e:
        log_system_event(
            level='ERROR',
            source='SYSTEM',
            message=f'Failed to export to ERP: {str(e)}',
            module='integrations.tasks',
            function='export_to_erp_task'
        )
        raise
