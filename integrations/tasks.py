"""
D365 integration tasks (synchronous — Celery disabled).
To re-enable async processing, convert these to Celery tasks with @shared_task.
"""
from system_logs.services import log_system_event


def push_application_to_d365_task(application_id):
    """Push a single application to D365 (runs synchronously)."""
    try:
        from integrations.services import Dynamics365ApplicantService
        Dynamics365ApplicantService.push_application(application_id)
    except Exception as e:
        log_system_event(
            level="ERROR", source="INTEGRATION",
            message=f"D365 push task failed for application {application_id}: {str(e)}",
            module="integrations.tasks", function="push_application_to_d365_task"
        )


def push_all_applications_for_job_task(job_advert_id, triggered_by_id=None):
    """Push all unpushed applications for a job to D365 (runs synchronously)."""
    try:
        from integrations.services import Dynamics365ApplicantService
        from accounts.models import User

        triggered_by = None
        if triggered_by_id:
            triggered_by = User.objects.filter(id=triggered_by_id).first()

        return Dynamics365ApplicantService.push_all_for_job(
            job_advert_id, triggered_by=triggered_by
        )
    except Exception as e:
        log_system_event(
            level="ERROR", source="INTEGRATION",
            message=f"D365 bulk push task failed for job {job_advert_id}: {str(e)}",
            module="integrations.tasks", function="push_all_applications_for_job_task"
        )
        return None
