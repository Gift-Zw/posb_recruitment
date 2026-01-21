"""
Application services for server-rendered flows.
"""
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from applications.models import ApplicantProfile, Application, ApplicationDocument
from notifications.tasks import send_application_submitted_email_task
from audit.services import log_audit_event


@transaction.atomic
def submit_application(applicant, job_advert, profile_form, application_form):
    """
    Create or update applicant profile and submit an application with snapshot.
    """
    if not job_advert.is_open_for_applications():
        raise ValidationError("Job is not accepting applications.")

    # Persist profile
    profile, _ = ApplicantProfile.objects.get_or_create(user=applicant)
    profile = profile_form.save(commit=False)
    profile.user = applicant
    profile.save()
    profile_form.save_m2m()

    # Build snapshot
    snapshot = {
        "phone_number": profile.phone_number,
        "address": profile.address,
        "date_of_birth": profile.date_of_birth.isoformat() if profile.date_of_birth else None,
        "nationality": profile.nationality,
        "education": profile.education,
        "experience": profile.experience,
        "skills": list(profile.skills.values_list("name", flat=True)),
        "cover_letter": profile.cover_letter,
    }

    # Reuse last application snapshot if requested and available
    if application_form.cleaned_data.get("reuse_last"):
        last = Application.objects.filter(applicant=applicant).order_by("-submitted_at").first()
        if last:
            snapshot = last.profile_snapshot

    application, _ = Application.objects.update_or_create(
        applicant=applicant,
        job_advert=job_advert,
        defaults={
            "profile_snapshot": snapshot,
            "status": "SUBMITTED",
            "submitted_at": timezone.now(),
            "ai_score": None,
            "ai_ranking": None,
            "ai_explanation": "",
        },
    )

    # Attach documents
    cv_file = application_form.cleaned_data["cv_file"]
    ApplicationDocument.objects.create(
        application=application,
        document_type="CV",
        file=cv_file,
        file_name=cv_file.name,
        file_size=cv_file.size,
    )

    # Audit + email
    log_audit_event(
        actor=applicant,
        action="APPLICATION_SUBMITTED",
        action_description=f"Application submitted for {job_advert.title}",
        entity=application,
    )
    send_application_submitted_email_task(application.id)

    return application
