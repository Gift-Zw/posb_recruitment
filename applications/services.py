"""
Application services for server-rendered flows.
"""
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from applications.models import ApplicantProfile, Application, ApplicationDocument, ApplicationData
from notifications.tasks import send_application_submitted_email_task
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
            "status": "SUBMITTED",
            "submitted_at": timezone.now(),
            "ai_score": None,
            "ai_ranking": None,
            "ai_explanation": "",
            "d365_push_status": "NOT_PUSHED",
        },
    )

    _create_application_data(application, profile, applicant)

    cv_file = application_form.cleaned_data["cv_file"]
    ApplicationDocument.objects.create(
        application=application,
        document_type="CV",
        file=cv_file,
        file_name=cv_file.name,
        file_size=cv_file.size,
    )

    log_audit_event(
        actor=applicant,
        action="APPLICATION_SUBMITTED",
        action_description=f"Application submitted for {job_advert.job_title}",
        entity=application,
    )
    send_application_submitted_email_task(application.id)

    # Queue D365 push as background task
    from integrations.tasks import push_application_to_d365_task
    push_application_to_d365_task(application.id)

    return application


def _create_application_data(application, profile, applicant):
    """Create immutable ApplicationData snapshot aligned with D365 Applicant Import fields."""
    skills_list = list(profile.skills.values_list("name", flat=True))
    skills_text = "; ".join(skills_list) if skills_list else ""
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
            "cover_letter": profile.cover_letter or "",
            "nationality": profile.citizenship.name if profile.citizenship else "",
            "education": profile.education if profile.education else [],
            "experience": profile.experience if profile.experience else [],
            "skills": skills_text,
        }
    )
