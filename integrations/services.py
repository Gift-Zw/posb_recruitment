"""
Dynamics 365 ERP integration service for POSB Recruitment Portal.
Handles export of shortlisted candidates to Dynamics 365.
"""
import requests
from django.conf import settings
from django.utils import timezone
from .models import ERPExport, ERPExportItem
from shortlisting.models import ShortlistingRun
from applications.models import Application
from audit.services import log_audit_event
from system_logs.services import log_system_event


class Dynamics365Service:
    """
    Service for integrating with Dynamics 365 ERP.
    This is a stub implementation - customize based on actual Dynamics 365 API.
    """
    
    @staticmethod
    def export_shortlisted_candidates(shortlisting_run_id, triggered_by=None):
        """
        Export shortlisted candidates to Dynamics 365 ERP.
        
        Args:
            shortlisting_run_id: ID of the shortlisting run
            triggered_by: User who triggered the export
        
        Returns:
            ERPExport instance
        """
        try:
            shortlisting_run = ShortlistingRun.objects.get(id=shortlisting_run_id)
            job_advert = shortlisting_run.job_advert
            
            # Get shortlisted applications
            shortlisted_applications = Application.objects.filter(
                job_advert=job_advert,
                status='SHORTLISTED',
                ai_shortlisted_at__isnull=False
            ).order_by('ai_ranking')
            
            if not shortlisted_applications.exists():
                log_system_event(
                    level='WARNING',
                    source='INTEGRATION',
                    message=f'No shortlisted candidates for export: {shortlisting_run_id}',
                    module='integrations.services',
                    function='export_shortlisted_candidates'
                )
                return None
            
            # Create ERP export record
            erp_export = ERPExport.objects.create(
                shortlisting_run=shortlisting_run,
                job_advert=job_advert,
                status='IN_PROGRESS',
                total_candidates=shortlisted_applications.count(),
                started_at=timezone.now()
            )
            
            # Get access token (OAuth 2.0)
            access_token = Dynamics365Service._get_access_token()
            
            # Export each candidate
            exported_count = 0
            failed_count = 0
            
            for application in shortlisted_applications:
                try:
                    export_item = ERPExportItem.objects.create(
                        export=erp_export,
                        application=application,
                        status='PENDING'
                    )
                    
                    # Prepare candidate data
                    candidate_data = Dynamics365Service._prepare_candidate_data(application)
                    
                    # Upload to Dynamics 365
                    response = Dynamics365Service._upload_to_dynamics365(
                        access_token,
                        candidate_data,
                        application
                    )
                    
                    # Update export item
                    export_item.status = 'EXPORTED'
                    export_item.erp_candidate_id = response.get('candidate_id', '')
                    export_item.erp_document_id = response.get('document_id', '')
                    export_item.exported_at = timezone.now()
                    export_item.save()
                    
                    exported_count += 1
                    
                except Exception as e:
                    if 'export_item' in locals():
                        export_item.status = 'FAILED'
                        export_item.error_message = str(e)
                        export_item.save()
                    
                    failed_count += 1
                    log_system_event(
                        level='ERROR',
                        source='INTEGRATION',
                        message=f'Failed to export candidate {application.id}: {str(e)}',
                        module='integrations.services',
                        function='export_shortlisted_candidates'
                    )
            
            # Update export status
            erp_export.exported_count = exported_count
            erp_export.failed_count = failed_count
            
            if failed_count == 0:
                erp_export.status = 'COMPLETED'
            elif exported_count > 0:
                erp_export.status = 'PARTIAL'
            else:
                erp_export.status = 'FAILED'
            
            erp_export.completed_at = timezone.now()
            erp_export.save()
            
            # Audit log
            log_audit_event(
                actor=triggered_by,
                action='ERP_EXPORT',
                action_description=f'Exported {exported_count} candidates to Dynamics 365',
                entity=erp_export,
                metadata={
                    'shortlisting_run_id': shortlisting_run_id,
                    'exported_count': exported_count,
                    'failed_count': failed_count
                }
            )
            
            return erp_export
            
        except ShortlistingRun.DoesNotExist:
            log_system_event(
                level='ERROR',
                source='INTEGRATION',
                message=f'Shortlisting run not found: {shortlisting_run_id}',
                module='integrations.services',
                function='export_shortlisted_candidates'
            )
            return None
        except Exception as e:
            if 'erp_export' in locals():
                erp_export.status = 'FAILED'
                erp_export.error_message = str(e)
                erp_export.completed_at = timezone.now()
                erp_export.save()
            
            log_system_event(
                level='ERROR',
                source='INTEGRATION',
                message=f'ERP export failed: {str(e)}',
                module='integrations.services',
                function='export_shortlisted_candidates'
            )
            raise
    
    @staticmethod
    def _get_access_token():
        """
        Get OAuth 2.0 access token for Dynamics 365 API.
        This is a stub - implement based on your Dynamics 365 authentication.
        """
        # TODO: Implement OAuth 2.0 flow
        # Example:
        # token_url = f"https://login.microsoftonline.com/{settings.DYNAMICS_365_TENANT_ID}/oauth2/v2.0/token"
        # data = {
        #     'client_id': settings.DYNAMICS_365_CLIENT_ID,
        #     'client_secret': settings.DYNAMICS_365_CLIENT_SECRET,
        #     'scope': 'https://your-dynamics-instance.crm.dynamics.com/.default',
        #     'grant_type': 'client_credentials'
        # }
        # response = requests.post(token_url, data=data)
        # return response.json()['access_token']
        
        return 'placeholder_token'
    
    @staticmethod
    def _prepare_candidate_data(application):
        """
        Prepare candidate data for Dynamics 365 API.
        Customize based on your Dynamics 365 entity structure.
        """
        # Get data from ApplicationData if available
        phone = ''
        if hasattr(application, 'application_data') and application.application_data:
            phone = application.application_data.phone_number or ''
        
        return {
            'first_name': application.applicant.first_name,
            'last_name': application.applicant.last_name,
            'email': application.applicant.email,
            'phone': phone,
            'job_title': application.job_advert.job_title,
            'ai_score': application.ai_score,
            'ai_ranking': application.ai_ranking,
            'application_id': application.id,
            'submitted_at': application.submitted_at.isoformat(),
        }
    
    @staticmethod
    def _upload_to_dynamics365(access_token, candidate_data, application):
        """
        Upload candidate data to Dynamics 365.
        This is a stub - implement based on your Dynamics 365 API.
        """
        # TODO: Implement actual Dynamics 365 API call
        # Example:
        # headers = {
        #     'Authorization': f'Bearer {access_token}',
        #     'Content-Type': 'application/json'
        # }
        # url = f"{settings.DYNAMICS_365_API_URL}/api/data/v9.2/contacts"
        # response = requests.post(url, json=candidate_data, headers=headers)
        # response.raise_for_status()
        # return response.json()
        
        # Placeholder response
        return {
            'candidate_id': f'D365-{application.id}',
            'document_id': f'DOC-{application.id}'
        }
