"""
D365 integration tasks (synchronous — Celery disabled).
To re-enable async processing, convert these to Celery tasks with @shared_task.
"""
from django.utils import timezone
from system_logs.services import log_system_event


def export_to_erp_task(shortlisting_run_id, triggered_by_id=None):
    """Export shortlisted candidates to ERP via D365 (runs synchronously)."""
    try:
        from integrations.models import ERPExport, ERPExportItem
        from shortlisting.models import ShortlistingRun
        from applications.models import Application
        from accounts.models import User

        run = ShortlistingRun.objects.select_related("job_advert").get(id=shortlisting_run_id)
        triggered_by = User.objects.filter(id=triggered_by_id).first() if triggered_by_id else None

        shortlisted = Application.objects.filter(
            job_advert=run.job_advert, status="SHORTLISTED"
        )

        export = ERPExport.objects.create(
            shortlisting_run=run,
            job_advert=run.job_advert,
            status="IN_PROGRESS",
            total_candidates=shortlisted.count(),
            started_at=timezone.now(),
        )

        exported = 0
        failed = 0
        for app in shortlisted:
            try:
                from integrations.services import Dynamics365ApplicantService
                result = Dynamics365ApplicantService.push_application(app.id, triggered_by=triggered_by)
                if result and result.d365_push_status in ("PUSHED", "DUPLICATE"):
                    ERPExportItem.objects.create(
                        export=export, application=app, status="EXPORTED",
                        erp_candidate_id=result.d365_applicant_id or "", exported_at=timezone.now(),
                    )
                    exported += 1
                else:
                    ERPExportItem.objects.create(
                        export=export, application=app, status="FAILED",
                        error_message=getattr(result, "d365_push_error", "Unknown error"),
                    )
                    failed += 1
            except Exception as item_err:
                ERPExportItem.objects.create(
                    export=export, application=app, status="FAILED",
                    error_message=str(item_err)[:500],
                )
                failed += 1

        export.exported_count = exported
        export.failed_count = failed
        export.status = "COMPLETED" if failed == 0 else ("FAILED" if exported == 0 else "COMPLETED")
        export.completed_at = timezone.now()
        export.save()

        log_system_event(
            level="INFO", source="INTEGRATION",
            message=f"ERP export for job '{run.job_advert.job_title}': {exported} exported, {failed} failed",
            module="integrations.tasks", function="export_to_erp_task",
        )
        return export

    except Exception as e:
        log_system_event(
            level="ERROR", source="INTEGRATION",
            message=f"ERP export task failed for shortlisting run {shortlisting_run_id}: {str(e)}",
            module="integrations.tasks", function="export_to_erp_task",
        )
        return None


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
