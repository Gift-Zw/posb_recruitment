"""
Server-rendered application views.
"""
import json
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, TemplateView
from jobs.models import JobAdvert
from applications.models import Application, ApplicantProfile
from applications.forms import ApplicantProfileForm, ApplicationForm
from applications.services import submit_application


class ApplicationListView(LoginRequiredMixin, ListView):
    """List applications for the logged-in applicant."""

    model = Application
    template_name = "applications/list.html"
    context_object_name = "applications"

    def dispatch(self, request, *args, **kwargs):
        """Prevent employees from viewing applications."""
        if request.user.is_employee():
            messages.error(request, "Employees cannot view applications. This feature is for applicants only.")
            return redirect("jobs:list")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Application.objects.filter(applicant=self.request.user).select_related("job_advert").order_by('-submitted_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        applications = context['applications']
        
        # Calculate statistics
        context['total_applications'] = applications.count()
        context['under_review'] = applications.filter(status='UNDER_REVIEW').count()
        context['shortlisted'] = applications.filter(status='SHORTLISTED').count()
        context['rejected'] = applications.filter(status='REJECTED').count()
        
        return context


class ApplicationDetailView(LoginRequiredMixin, DetailView):
    """View a single application belonging to the user."""

    model = Application
    template_name = "applications/detail.html"
    context_object_name = "application"

    def dispatch(self, request, *args, **kwargs):
        """Prevent employees from viewing applications."""
        if request.user.is_employee():
            messages.error(request, "Employees cannot view applications. This feature is for applicants only.")
            return redirect("jobs:list")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Application.objects.filter(applicant=self.request.user).select_related("job_advert")


class ApplyView(LoginRequiredMixin, TemplateView):
    """Apply to a job advert."""

    template_name = "applications/apply.html"

    def dispatch(self, request, *args, **kwargs):
        """Prevent employees from applying for jobs."""
        if request.user.is_employee():
            messages.error(request, "Employees cannot apply for jobs. This feature is for applicants only.")
            return redirect("jobs:list")
        if not request.user.is_verified:
            messages.error(request, "Please verify your email before applying for jobs.")
            return redirect("otp-verify")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        job = get_object_or_404(JobAdvert, pk=kwargs["job_id"])
        if not job.is_open_for_applications():
            messages.error(request, "This vacancy is closed and no longer accepting applications.")
            return redirect("jobs:list")
        
        # Check if user has already applied to this job
        existing_application = Application.objects.filter(
            applicant=request.user,
            job_advert=job
        ).first()
        
        if existing_application:
            messages.info(
                request,
                f"You have already applied for this position. Your application was submitted on {existing_application.submitted_at.strftime('%B %d, %Y')} and is currently {existing_application.get_status_display().lower()}."
            )
            return redirect("applications:detail", pk=existing_application.pk)
        
        profile = getattr(request.user, "applicant_profile", None)
        initial_profile = {}
        if profile:
            email = profile.email if profile.email else request.user.email
            skills_list = [skill.name for skill in profile.skills.all()]
            skills_text = "; ".join(skills_list) if skills_list else ""
            
            initial_profile = {
                "phone_number": profile.phone_number,
                "alternate_phone": profile.alternate_phone,
                "email": email,
                "middle_name": profile.middle_name,
                "date_of_birth": profile.date_of_birth,
                "gender": profile.gender,
                "citizenship": profile.citizenship_id,
                "id_number": profile.id_number,
                "marital_status": profile.marital_status,
                "current_job_title": profile.current_job_title,
                "education_level": profile.education_level_id,
                "address_line_1": profile.address_line_1,
                "address_line_2": profile.address_line_2,
                "city": profile.city,
                "state_province": profile.state_province,
                "postal_code": profile.postal_code,
                "country": profile.country_id,
                "professional_summary": profile.professional_summary,
                "skills_text": skills_text,
                "cover_letter": profile.cover_letter,
                "linkedin_url": profile.linkedin_url,
                "portfolio_url": profile.portfolio_url,
                "availability_date": profile.availability_date,
                "current_salary": profile.current_salary,
                "expected_salary": profile.expected_salary,
                "notice_period": profile.notice_period,
            }
        else:
            initial_profile = {
                "email": request.user.email,
            }
        context = {
            "job": job,
            "profile_form": ApplicantProfileForm(initial=initial_profile),
            "application_form": ApplicationForm(),
        }
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        job = get_object_or_404(JobAdvert, pk=kwargs["job_id"])
        if not job.is_open_for_applications():
            messages.error(request, "This vacancy is closed and no longer accepting applications.")
            return redirect("jobs:list")
        
        # Check if user has already applied to this job
        existing_application = Application.objects.filter(
            applicant=request.user,
            job_advert=job
        ).first()
        
        if existing_application:
            messages.info(
                request,
                f"You have already applied for this position. Your application was submitted on {existing_application.submitted_at.strftime('%B %d, %Y')} and is currently {existing_application.get_status_display().lower()}."
            )
            return redirect("applications:detail", pk=existing_application.pk)
        
        profile_form = ApplicantProfileForm(request.POST, instance=getattr(request.user, "applicant_profile", None))
        application_form = ApplicationForm(request.POST, request.FILES)

        if profile_form.is_valid() and application_form.is_valid():
            try:
                # Handle skills_text - convert semicolon-separated string to Skill objects
                skills_text = profile_form.cleaned_data.get('skills_text', '').strip()
                skill_objects = []
                if skills_text:
                    from jobs.models import Skill
                    skill_names = [s.strip() for s in skills_text.split(';') if s.strip()]
                    # Get or create skills
                    for skill_name in skill_names:
                        skill, _ = Skill.objects.get_or_create(name=skill_name)
                        skill_objects.append(skill)
                
                # Save profile with skills
                profile = profile_form.save(commit=False)
                profile.user = request.user
                profile.save()
                profile.skills.set(skill_objects)
                
                # Now submit application (it will use the already-saved profile)
                submit_application(request.user, job, profile_form, application_form)
                messages.success(request, "Application submitted successfully.")
                return redirect("applications:list")
            except Exception as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "Please correct the errors below.")

        context = {
            "job": job,
            "profile_form": profile_form,
            "application_form": application_form,
        }
        return self.render_to_response(context)
