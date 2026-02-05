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
    """
    if not job_advert.is_open_for_applications():
        raise ValidationError("Job is not accepting applications.")

    # Persist profile (may already be saved with skills from view)
    profile, _ = ApplicantProfile.objects.get_or_create(user=applicant)
    # Only update if form has changes (skills are already handled in view)
    profile = profile_form.save(commit=False)
    profile.user = applicant
    profile.save()
    # Only call save_m2m if form has ManyToMany fields (skills is handled separately)
    try:
        profile_form.save_m2m()
    except ValueError:
        # If form doesn't have m2m fields, that's fine - skills are already set
        pass

    # Create or update application
    application, _ = Application.objects.update_or_create(
        applicant=applicant,
        job_advert=job_advert,
        defaults={
            "status": "SUBMITTED",
            "submitted_at": timezone.now(),
            "ai_score": None,
            "ai_ranking": None,
            "ai_explanation": "",
        },
    )

    # Check if we should reuse last application data
    reuse_last = application_form.cleaned_data.get("reuse_last", False)
    if reuse_last:
        last_application = Application.objects.filter(applicant=applicant).exclude(id=application.id).order_by("-submitted_at").first()
        if last_application and hasattr(last_application, 'application_data'):
            # Copy data from last application
            last_data = last_application.application_data
            ApplicationData.objects.update_or_create(
                application=application,
                defaults={
                    "phone_number": last_data.phone_number,
                    "email": last_data.email,
                    "address": last_data.address,
                    "date_of_birth": last_data.date_of_birth,
                    "nationality": last_data.nationality,
                    "education": last_data.education,
                    "experience": last_data.experience,
                    "skills": last_data.skills,
                    "cover_letter": last_data.cover_letter,
                }
            )
        else:
            # No previous data, create from current profile
            _create_application_data(application, profile)
    else:
        # Create application data from current profile
        _create_application_data(application, profile)

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
        action_description=f"Application submitted for {job_advert.job_title}",
        entity=application,
    )
    send_application_submitted_email_task(application.id)

    return application


def _create_application_data(application, profile):
    """Helper function to create ApplicationData from ApplicantProfile."""
    # Build address string from address fields
    address_parts = []
    if profile.address_line_1:
        address_parts.append(profile.address_line_1)
    if profile.address_line_2:
        address_parts.append(profile.address_line_2)
    if profile.city:
        address_parts.append(profile.city)
    if profile.state_province:
        address_parts.append(profile.state_province)
    if profile.country:
        address_parts.append(profile.country)
    address = ", ".join(address_parts) if address_parts else ""
    
    # Convert skills to semicolon-separated string
    skills_list = list(profile.skills.values_list("name", flat=True))
    skills_text = "; ".join(skills_list) if skills_list else ""
    
    # Use profile email if available, otherwise use user email
    email = profile.email if profile.email else application.applicant.email
    
    ApplicationData.objects.update_or_create(
        application=application,
        defaults={
            "phone_number": profile.phone_number or "",
            "email": email,
            "address": address,
            "date_of_birth": profile.date_of_birth,
            "nationality": profile.nationality or "",
            "education": profile.education if profile.education else [],
            "experience": profile.experience if profile.experience else [],
            "skills": skills_text,
            "cover_letter": profile.cover_letter or "",
        }
    )
