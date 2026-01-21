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
        return Application.objects.filter(applicant=self.request.user).select_related("job_advert", "job_advert__category").order_by('-submitted_at')
    
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
        profile = getattr(request.user, "applicant_profile", None)
        initial_profile = {}
        if profile:
            # Use profile email if available, otherwise use user email
            email = profile.email if profile.email else request.user.email
            initial_profile = {
                "phone_number": profile.phone_number,
                "alternate_phone": profile.alternate_phone,
                "email": email,
                "date_of_birth": profile.date_of_birth,
                "gender": profile.gender,
                "nationality": profile.nationality,
                "id_number": profile.id_number,
                "marital_status": profile.marital_status,
                "address_line_1": profile.address_line_1,
                "address_line_2": profile.address_line_2,
                "city": profile.city,
                "state_province": profile.state_province,
                "postal_code": profile.postal_code,
                "country": profile.country,
                "professional_summary": profile.professional_summary,
                "education": json.dumps(profile.education) if profile.education else "",
                "experience": json.dumps(profile.experience) if profile.experience else "",
                "skills": profile.skills.all(),
                "languages": json.dumps(profile.languages) if profile.languages else "",
                "certifications": json.dumps(profile.certifications) if profile.certifications else "",
                "references": json.dumps(profile.references) if profile.references else "",
                "emergency_contact_name": profile.emergency_contact_name,
                "emergency_contact_relationship": profile.emergency_contact_relationship,
                "emergency_contact_phone": profile.emergency_contact_phone,
                "emergency_contact_email": profile.emergency_contact_email,
                "cover_letter": profile.cover_letter,
                "linkedin_url": profile.linkedin_url,
                "portfolio_url": profile.portfolio_url,
                "availability_date": profile.availability_date,
                "current_salary": profile.current_salary,
                "expected_salary": profile.expected_salary,
                "notice_period": profile.notice_period,
            }
        else:
            # If no profile exists, at least populate email from user
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
        profile_form = ApplicantProfileForm(request.POST, instance=getattr(request.user, "applicant_profile", None))
        application_form = ApplicationForm(request.POST, request.FILES)

        if profile_form.is_valid() and application_form.is_valid():
            try:
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
