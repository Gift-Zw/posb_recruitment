"""
AI Shortlisting service for POSB Recruitment Portal.
Handles candidate ranking and shortlisting using AI.
"""
from django.utils import timezone
from .models import ShortlistingRun
from applications.models import Application
from jobs.models import JobAdvert
from notifications.tasks import send_shortlisted_email_task, send_rejected_email_task
from audit.services import log_audit_event
from system_logs.services import log_system_event


class AIShortlistingService:
    """
    AI-powered shortlisting service.
    This is a stub implementation - integrate with your AI service (OpenAI, custom ML model, etc.)
    """
    
    @staticmethod
    def shortlist_candidates(job_advert_id, triggered_by=None, trigger_type='AUTOMATIC'):
        """
        Perform AI shortlisting for a job advert.
        
        Args:
            job_advert_id: ID of the job advert
            triggered_by: User who triggered (None for automatic)
            trigger_type: 'AUTOMATIC' or 'MANUAL'
        
        Returns:
            ShortlistingRun instance
        """
        try:
            job_advert = JobAdvert.objects.get(id=job_advert_id)
            
            # Get all applications for this job
            applications = Application.objects.filter(
                job_advert=job_advert,
                status__in=['SUBMITTED', 'UNDER_REVIEW']
            )
            
            total_applications = applications.count()
            
            if total_applications == 0:
                log_system_event(
                    level='WARNING',
                    source='SYSTEM',
                    message=f'No applications found for job {job_advert_id}',
                    module='shortlisting.services',
                    function='shortlist_candidates'
                )
                return None
            
            # Create shortlisting run
            shortlisting_run = ShortlistingRun.objects.create(
                job_advert=job_advert,
                triggered_by=triggered_by,
                trigger_type=trigger_type,
                status='IN_PROGRESS',
                shortlist_count=job_advert.shortlist_count,
                total_applications=total_applications,
                started_at=timezone.now()
            )
            
            # Perform AI scoring and ranking
            scored_applications = AIShortlistingService._score_applications(
                applications,
                job_advert
            )
            
            # Rank applications by score
            ranked_applications = sorted(
                scored_applications,
                key=lambda x: x['score'],
                reverse=True
            )
            
            # Update rankings
            for rank, app_data in enumerate(ranked_applications, start=1):
                application = app_data['application']
                application.ai_score = app_data['score']
                application.ai_ranking = rank
                application.ai_explanation = app_data.get('explanation', '')
                application.ai_shortlisted_at = timezone.now()
                
                # Update status based on ranking
                if rank <= job_advert.shortlist_count:
                    application.status = 'SHORTLISTED'
                    shortlisting_run.shortlisted_count += 1
                else:
                    application.status = 'REJECTED'
                
                application.save()
            
            # Complete shortlisting run
            shortlisting_run.status = 'COMPLETED'
            shortlisting_run.completed_at = timezone.now()
            shortlisting_run.save()
            
            # Send notifications
            shortlisted_apps = Application.objects.filter(
                job_advert=job_advert,
                status='SHORTLISTED',
                ai_shortlisted_at__isnull=False
            )
            
            for app in shortlisted_apps:
                send_shortlisted_email_task(app.id)
            
            rejected_apps = Application.objects.filter(
                job_advert=job_advert,
                status='REJECTED',
                ai_shortlisted_at__isnull=False
            )
            
            for app in rejected_apps:
                send_rejected_email_task(app.id)
            
            # Audit log
            log_audit_event(
                actor=triggered_by,
                action='AI_SHORTLISTING',
                action_description=f'AI shortlisting completed for {job_advert.title}',
                entity=shortlisting_run,
                metadata={
                    'job_advert_id': job_advert_id,
                    'total_applications': total_applications,
                    'shortlisted_count': shortlisting_run.shortlisted_count
                }
            )
            
            return shortlisting_run
            
        except JobAdvert.DoesNotExist:
            log_system_event(
                level='ERROR',
                source='SYSTEM',
                message=f'Job advert not found: {job_advert_id}',
                module='shortlisting.services',
                function='shortlist_candidates'
            )
            return None
        except Exception as e:
            if 'shortlisting_run' in locals():
                shortlisting_run.status = 'FAILED'
                shortlisting_run.error_message = str(e)
                shortlisting_run.completed_at = timezone.now()
                shortlisting_run.save()
            
            log_system_event(
                level='ERROR',
                source='SYSTEM',
                message=f'AI shortlisting failed: {str(e)}',
                module='shortlisting.services',
                function='shortlist_candidates'
            )
            raise
    
    @staticmethod
    def _score_applications(applications, job_advert):
        """
        Score applications using AI.
        This is a stub - replace with actual AI integration.
        
        Returns:
            List of dicts: [{'application': Application, 'score': float, 'explanation': str}]
        """
        scored = []
        
        # Extract job requirements
        required_skills = list(job_advert.required_skills.values_list('name', flat=True))
        job_description = job_advert.description
        job_responsibilities = job_advert.responsibilities
        ai_instructions = job_advert.ai_shortlisting_instructions
        
        for application in applications:
            # Extract applicant data from snapshot
            profile = application.profile_snapshot
            applicant_skills = profile.get('skills', [])
            applicant_experience = profile.get('experience', [])
            applicant_education = profile.get('education', [])
            
            # TODO: Integrate with actual AI service (OpenAI, custom ML model, etc.)
            # For now, using a simple scoring algorithm as placeholder
            
            score = AIShortlistingService._calculate_placeholder_score(
                required_skills,
                applicant_skills,
                applicant_experience,
                applicant_education,
                job_description
            )
            
            explanation = f"Score based on skills match ({len(set(required_skills) & set(applicant_skills))}/{len(required_skills)}), experience, and education."
            
            scored.append({
                'application': application,
                'score': score,
                'explanation': explanation
            })
        
        return scored
    
    @staticmethod
    def _calculate_placeholder_score(required_skills, applicant_skills, experience, education, job_description):
        """
        Placeholder scoring algorithm.
        Replace this with actual AI integration.
        """
        score = 50.0  # Base score
        
        # Skills match (40% weight)
        if required_skills:
            matched_skills = len(set(required_skills) & set(applicant_skills))
            skills_score = (matched_skills / len(required_skills)) * 40
            score += skills_score
        
        # Experience (30% weight)
        if experience:
            experience_score = min(len(experience) * 5, 30)
            score += experience_score
        
        # Education (20% weight)
        if education:
            education_score = min(len(education) * 10, 20)
            score += education_score
        
        # Random variation for demonstration (remove in production)
        import random
        score += random.uniform(-5, 5)
        
        return min(max(score, 0), 100)  # Clamp between 0 and 100
