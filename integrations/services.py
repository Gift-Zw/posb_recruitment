"""
D365 Applicant Import API integration service.
Pushes applicant data to D365 Finance & Operations HCM via the SubmitApplicant custom service.
"""
import logging
import requests
from django.conf import settings
from django.utils import timezone
from applications.models import Application
from audit.services import log_audit_event
from system_logs.services import log_system_event

logger = logging.getLogger(__name__)


class Dynamics365ApplicantService:
    """
    Service for pushing applicant data to D365 F&O via the SubmitApplicant endpoint.
    Payload follows PascalCase convention wrapped in a 'contract' key.
    """

    @staticmethod
    def get_access_token():
        """Acquire OAuth 2.0 Bearer token from Azure AD for D365 F&O."""
        tenant_id = settings.DYNAMICS_365_TENANT_ID
        client_id = settings.DYNAMICS_365_CLIENT_ID
        client_secret = settings.DYNAMICS_365_CLIENT_SECRET
        resource = settings.DYNAMICS_365_API_URL

        if not all([tenant_id, client_id, client_secret, resource]):
            raise ValueError("D365 credentials not configured. Check environment variables.")

        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "resource": resource,
        }

        response = requests.post(token_url, data=data, timeout=30)
        response.raise_for_status()
        return response.json()["access_token"]

    @staticmethod
    def build_applicant_payload(application):
        """
        Build the PascalCase JSON payload for the SubmitApplicant endpoint.
        Uses data from ApplicationData (immutable snapshot).
        """
        app_data = application.application_data

        # Generate a unique applicant ID: POSB-AI-XXXXX
        if not application.d365_applicant_id:
            application.d365_applicant_id = f"POSB-AI-{application.id:05d}"
            application.save(update_fields=["d365_applicant_id"])

        payload = {
            "contract": {
                "ApplicantId": application.d365_applicant_id,
                "RecruitingId": application.job_advert.recruiting_id,
                "FirstName": app_data.first_name,
                "LastName": app_data.last_name,
                "MiddleName": app_data.middle_name or "",
                "Email": app_data.email,
                "Phone": app_data.phone_number or "",
                "BirthDateUtc": app_data.date_of_birth.isoformat() if app_data.date_of_birth else "",
                "Gender": app_data.gender or "",
                "Citizenship": app_data.citizenship or "",
                "MaritalStatus": app_data.marital_status or "",
                "StreetAddress": app_data.street_address or "",
                "City": app_data.city or "",
                "ZipCode": app_data.zip_code or "",
                "Country": app_data.country or "",
                "CurrentJobTitle": app_data.current_job_title or "",
                "EducationLevelDescription": app_data.education_level or "",
                "CoverLetter": app_data.cover_letter or "",
            }
        }
        return payload

    @staticmethod
    def push_application(application_id, triggered_by=None):
        """
        Push a single application to D365.
        Updates the application's d365_push_status based on the response.
        """
        try:
            application = Application.objects.select_related(
                "applicant", "job_advert"
            ).get(id=application_id)
        except Application.DoesNotExist:
            log_system_event(
                level="ERROR", source="INTEGRATION",
                message=f"Application {application_id} not found for D365 push",
                module="integrations.services", function="push_application"
            )
            return None

        if not hasattr(application, "application_data"):
            application.d365_push_status = "FAILED"
            application.d365_push_error = "No application data snapshot found"
            application.save(update_fields=["d365_push_status", "d365_push_error"])
            return application

        application.d365_push_status = "PENDING"
        application.d365_push_attempts += 1
        application.save(update_fields=["d365_push_status", "d365_push_attempts"])

        try:
            access_token = Dynamics365ApplicantService.get_access_token()
            payload = Dynamics365ApplicantService.build_applicant_payload(application)

            api_url = f"{settings.DYNAMICS_365_API_URL.rstrip('/')}/api/services/POSBRecruitmentServiceGroup/POSBRecruitmentService/SubmitApplicant"

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

            response = requests.post(api_url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()

            result = response.json()

            # D365 returns parmStatus: "Created" or "Duplicate"
            parm_status = ""
            applicant_rec_id = None
            application_rec_id = None

            if isinstance(result, dict):
                parm_status = result.get("parmStatus", result.get("Status", ""))
                applicant_rec_id = result.get("parmApplicantRecId") or result.get("ApplicantRecId")
                application_rec_id = result.get("parmApplicationRecId") or result.get("ApplicationRecId")

            if parm_status.lower() == "duplicate":
                application.d365_push_status = "DUPLICATE"
            else:
                application.d365_push_status = "PUSHED"

            application.d365_pushed_at = timezone.now()
            application.d365_push_error = ""
            if applicant_rec_id:
                application.d365_applicant_rec_id = int(applicant_rec_id)
            if application_rec_id:
                application.d365_application_rec_id = int(application_rec_id)
            application.save()

            log_audit_event(
                actor=triggered_by,
                action="D365_PUSH",
                action_description=f"Application {application.id} pushed to D365 ({parm_status})",
                entity=application,
                metadata={
                    "applicant_id": application.d365_applicant_id,
                    "status": parm_status,
                    "rec_id": applicant_rec_id,
                }
            )

            log_system_event(
                level="INFO", source="INTEGRATION",
                message=f"D365 push success: Application {application.id} -> {parm_status}",
                module="integrations.services", function="push_application"
            )

            return application

        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_msg = f"{e.response.status_code}: {e.response.text[:500]}"
                except Exception:
                    pass

            application.d365_push_status = "FAILED"
            application.d365_push_error = error_msg
            application.save(update_fields=["d365_push_status", "d365_push_error"])

            log_system_event(
                level="ERROR", source="INTEGRATION",
                message=f"D365 push failed for application {application_id}: {error_msg}",
                module="integrations.services", function="push_application"
            )
            return application

        except Exception as e:
            application.d365_push_status = "FAILED"
            application.d365_push_error = str(e)[:500]
            application.save(update_fields=["d365_push_status", "d365_push_error"])

            log_system_event(
                level="ERROR", source="INTEGRATION",
                message=f"D365 push error for application {application_id}: {str(e)}",
                module="integrations.services", function="push_application"
            )
            return application

    @staticmethod
    def push_all_for_job(job_advert_id, triggered_by=None):
        """
        Push all applications for a job to D365.
        Used when closing a job to eliminate first-applied bias.
        Returns summary dict.
        """
        applications = Application.objects.filter(
            job_advert_id=job_advert_id,
            status="SUBMITTED",
        ).exclude(
            d365_push_status="PUSHED"
        ).order_by("submitted_at")

        total = applications.count()
        pushed = 0
        failed = 0
        duplicates = 0

        for application in applications:
            result = Dynamics365ApplicantService.push_application(
                application.id, triggered_by=triggered_by
            )
            if result:
                if result.d365_push_status == "PUSHED":
                    pushed += 1
                elif result.d365_push_status == "DUPLICATE":
                    duplicates += 1
                else:
                    failed += 1
            else:
                failed += 1

        summary = {
            "total": total,
            "pushed": pushed,
            "duplicates": duplicates,
            "failed": failed,
        }

        log_audit_event(
            actor=triggered_by,
            action="D365_BULK_PUSH",
            action_description=f"Bulk D365 push for job {job_advert_id}: {pushed} pushed, {duplicates} duplicates, {failed} failed",
            metadata=summary
        )

        return summary
