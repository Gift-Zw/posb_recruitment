"""
Application services for server-rendered flows.
"""
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings
from applications.models import ApplicantProfile, Application, ApplicationDocument, ApplicationData
from notifications.tasks import enqueue_send_application_submitted_email_task
from audit.services import log_audit_event


@transaction.atomic
def submit_application(applicant, job_advert, profile_form, application_form):
    """
    Create or update applicant profile and submit an application with immutable data.
    After submission, triggers a background task to push to D365.
    """
    if not job_advert.is_open_for_applications():
        raise ValidationError("Job is not accepting applications.")

    profile, _ = ApplicantProfile.objects.get_or_create(user=applicant)
    profile = profile_form.save(commit=False)
    profile.user = applicant
    profile.save()
    try:
        profile_form.save_m2m()
    except ValueError:
        pass

    application, _ = Application.objects.update_or_create(
        applicant=applicant,
        job_advert=job_advert,
        defaults={
            "status": "PENDING_UPLOAD",
            "submitted_at": timezone.now(),
            "d365_push_status": "NOT_PUSHED",
        },
    )

    _create_application_data(
        application,
        profile,
        applicant,
        cover_letter=application_form.cleaned_data.get("cover_letter", ""),
    )

    cv_file = application_form.cleaned_data["cv_file"]
    ApplicationDocument.objects.create(
        application=application,
        document_type="CV",
        file=cv_file,
        file_name=cv_file.name,
        file_size=cv_file.size,
    )
    # Persist file metadata immediately. FileBytes is intentionally deferred to background
    # D365 push flow to avoid request-time base64 conversion overhead.
    ApplicationData.objects.filter(application=application).update(
        file_name=cv_file.name,
    )

    log_audit_event(
        actor=applicant,
        action="APPLICATION_SUBMITTED",
        action_description=f"Application submitted for {job_advert.job_title}",
        entity=application,
    )
    enqueue_send_application_submitted_email_task(application.id)

    # Optional auto-push to D365 on submission (async fire-and-forget),
    # but only once HR has approved the application.
    if settings.D365_PUSH_ON_SUBMISSION and application.review_status == "APPROVED":
        from integrations.tasks import enqueue_push_application_to_d365_task
        enqueue_push_application_to_d365_task(application.id)

    return application


def _create_application_data(application, profile, applicant, cover_letter=""):
    """Create immutable ApplicationData snapshot aligned with D365 Applicant Import fields."""
    email = profile.email if profile.email else applicant.email

    street_parts = [profile.address_line_1, profile.address_line_2]
    street_address = ", ".join(p for p in street_parts if p)

    ApplicationData.objects.update_or_create(
        application=application,
        defaults={
            "first_name": applicant.first_name or "",
            "last_name": applicant.last_name or "",
            "middle_name": profile.middle_name or "",
            "email": email,
            "phone_number": profile.phone_number or "",
            "date_of_birth": profile.date_of_birth,
            "gender": profile.gender or "",
            "citizenship": profile.citizenship.iso3 if profile.citizenship else "",
            "marital_status": profile.marital_status or "",
            "street_address": street_address,
            "city": profile.city or "",
            "zip_code": profile.postal_code or "",
            "country": profile.country.iso2 if profile.country else "",
            "current_job_title": profile.current_job_title or "",
            "education_level": profile.education_level.name if profile.education_level else "",
            "external_application_id": f"EXT-{application.id:06d}",
            "cover_letter": cover_letter or profile.cover_letter or "",
        }
    )
