"""
Server-rendered views for jobs app.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, TemplateView, FormView
from .models import Skill, JobAdvert
from .forms import SkillForm, ContactForm
from audit.services import log_audit_event
from system_logs.services import log_system_event


class HRStaffRequiredMixin(UserPassesTestMixin):
    """Ensure the user is an employee (HR staff). Blocks applicants from accessing management URLs."""

    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        # Only employees and superusers can access
        if self.request.user.is_applicant():
            return False
        return self.request.user.is_employee() or self.request.user.is_superuser

    def handle_no_permission(self):
        if self.request.user.is_authenticated and self.request.user.is_applicant():
            messages.error(self.request, "This area is for HR staff only. Applicants cannot access the management portal.")
            from django.shortcuts import redirect
            return redirect("jobs:list")
        messages.error(self.request, "Employee access required. Please log in with an HR staff account.")
        from django.shortcuts import redirect
        return redirect("management:login")


class HomeView(TemplateView):
    """Home/landing page."""
    template_name = "home.html"


class FAQsView(FormView):
    """Frequently Asked Questions page with contact form."""
    template_name = "jobs/faqs.html"
    form_class = ContactForm
    success_url = reverse_lazy("jobs:faqs")
    
    def form_valid(self, form):
        """Handle contact form submission."""
        name = form.cleaned_data['name']
        email = form.cleaned_data['email']
        subject = form.cleaned_data['subject']
        message = form.cleaned_data['message']
        
        # Send email to HR team synchronously
        try:
            send_mail(
                subject=f'FAQ Query: {subject}',
                message=f'Name: {name}\nEmail: {email}\n\nMessage:\n{message}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.HR_CONTACT_EMAIL],  # Send to HR team
                fail_silently=False
            )
            
            # Audit log
            log_audit_event(
                actor=None,
                action='CONTACT_FORM_SUBMITTED',
                action_description=f'Contact form submitted by {name} ({email})',
                metadata={'subject': subject, 'email': email}
            )
            
            messages.success(self.request, 'Thank you for your query! We will get back to you soon.')
        except (TimeoutError, ConnectionError, OSError) as e:
            # Network-related errors (timeout, connection refused, etc.)
            log_system_event(
                level='ERROR',
                source='SYSTEM',
                message=f'Network error sending FAQ contact form email: {str(e)}',
                module='jobs.views',
                function='FAQsView.form_valid'
            )
            messages.error(
                self.request,
                "We're experiencing network issues. Your message has been saved, but we couldn't send it right now. Please try again later or contact us directly."
            )
        except Exception as e:
            # Other email errors
            log_system_event(
                level='ERROR',
                source='SYSTEM',
                message=f'Failed to send FAQ contact form email: {str(e)}',
                module='jobs.views',
                function='FAQsView.form_valid'
            )
            messages.error(
                self.request,
                'Sorry, there was an error sending your message. Please try again later or contact us directly.'
            )
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'form' not in context:
            context['form'] = self.get_form()
        return context


class JobListView(ListView):
    """Public job listings (OPEN only)."""

    model = JobAdvert
    template_name = "jobs/list.html"
    context_object_name = "jobs"
    paginate_by = 10

    def get_queryset(self):
        now = timezone.now()
        queryset = JobAdvert.objects.filter(status="OPEN").order_by("-created_at")
        queryset = queryset.filter(Q(end_date__isnull=True) | Q(end_date__gt=now))
        
        # Search by title, function, or description
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(job_title__icontains=search) |
                Q(job_function__icontains=search) |
                Q(job_description__icontains=search)
            )
        
        # Filter by job function (multiple allowed)
        functions = self.request.GET.getlist('job_function')
        if functions:
            queryset = queryset.filter(job_function__in=functions)
        
        # Filter by location/city (multiple allowed)
        locations = self.request.GET.getlist('location')
        if locations:
            queryset = queryset.filter(location__in=locations)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        
        # Get job functions with open job counts
        context['job_functions'] = (
            JobAdvert.objects.filter(status='OPEN')
            .filter(Q(end_date__isnull=True) | Q(end_date__gt=now))
            .exclude(job_function='')
            .values('job_function')
            .annotate(job_count=Count('id'))
            .order_by('job_function')
        )
        context['selected_job_functions'] = self.request.GET.getlist('job_function')
        
        # Get distinct locations from open jobs with counts
        location_counts = (
            JobAdvert.objects.filter(status='OPEN')
            .filter(Q(end_date__isnull=True) | Q(end_date__gt=now))
            .exclude(location='')
            .values('location')
            .annotate(job_count=Count('id'))
            .order_by('location')
        )
        context['locations'] = location_counts
        context['selected_locations'] = self.request.GET.getlist('location')
        
        # Check which jobs the user has already applied to (if authenticated and is applicant)
        if self.request.user.is_authenticated and self.request.user.is_applicant():
            from applications.models import Application
            # Get the actual job objects from the context (could be from page_obj or jobs)
            jobs_list = context.get('jobs', [])
            if 'page_obj' in context and hasattr(context['page_obj'], 'object_list'):
                jobs_list = context['page_obj'].object_list
            
            # Extract job IDs - handle both queryset and list
            if jobs_list:
                if hasattr(jobs_list, 'values_list'):
                    # It's a queryset
                    job_ids = list(jobs_list.values_list('pk', flat=True))
                else:
                    # It's a list of objects
                    job_ids = [job.pk for job in jobs_list]
            else:
                job_ids = []
            
            if job_ids:
                applications = Application.objects.filter(
                    applicant=self.request.user,
                    job_advert_id__in=job_ids
                ).select_related('job_advert')
                
                # Create a dictionary mapping job_id to application
                applied_jobs_dict = {app.job_advert_id: app for app in applications}
                context['applied_jobs_dict'] = applied_jobs_dict
                context['applied_job_ids'] = list(applied_jobs_dict.keys())  # Use list for template compatibility
            else:
                context['applied_jobs_dict'] = {}
                context['applied_job_ids'] = []
        else:
            context['applied_jobs_dict'] = {}
            context['applied_job_ids'] = []
        
        return context


class JobDetailView(DetailView):
    """Job detail view."""

    model = JobAdvert
    template_name = "jobs/detail.html"
    context_object_name = "job"

    def get_queryset(self):
        qs = JobAdvert.objects.all()
        if not self.request.user.is_authenticated or (not self.request.user.is_employee() and not self.request.user.is_superuser):
            now = timezone.now()
            qs = qs.filter(status="OPEN").filter(Q(end_date__isnull=True) | Q(end_date__gt=now))
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Check if user has already applied to this job
        if self.request.user.is_authenticated and self.request.user.is_applicant():
            from applications.models import Application
            existing_application = Application.objects.filter(
                applicant=self.request.user,
                job_advert=self.object
            ).first()
            context['existing_application'] = existing_application
        
        return context


class ManagementDashboardView(HRStaffRequiredMixin, TemplateView):
    """Management dashboard with statistics and overview."""

    template_name = "management/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from applications.models import Application
        
        # Job statistics
        context['total_jobs'] = JobAdvert.objects.count()
        context['open_jobs'] = JobAdvert.objects.filter(status='OPEN').count()
        context['closed_jobs'] = JobAdvert.objects.filter(status='CLOSED').count()
        
        # Application statistics
        context['total_applications'] = Application.objects.count()
        
        # Recent job adverts
        context['recent_jobs'] = JobAdvert.objects.prefetch_related('applications').order_by('-created_at')[:5]
        
        # Recent applications
        context['recent_applications'] = Application.objects.select_related('applicant', 'job_advert').order_by('-submitted_at')[:5]
        
        return context


class JobAdvertListView(HRStaffRequiredMixin, ListView):
    """List all job adverts for HR management."""

    model = JobAdvert
    template_name = "management/jobs/list.html"
    context_object_name = "jobs"
    paginate_by = 20

    def get_queryset(self):
        from django.db.models import Count, Q
        
        queryset = JobAdvert.objects.prefetch_related("applications").annotate(
            application_count=Count('applications'),
            shortlisted_count=Count('applications', filter=Q(applications__status='SHORTLISTED'))
        ).order_by("-created_at")
        
        # Filter by status
        status = self.request.GET.get('status')
        if status in ['OPEN', 'CLOSED']:
            queryset = queryset.filter(status=status)
        
        # Search by title, job ID, or function
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(job_title__icontains=search) |
                Q(job_id__icontains=search) |
                Q(job_function__icontains=search)
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')
        
        # Application counts are already annotated in the queryset
        return context


class JobAdvertDetailView(HRStaffRequiredMixin, DetailView):
    """Job advert detail view for HR management."""

    model = JobAdvert
    template_name = "management/jobs/detail.html"
    context_object_name = "job"

    def get_queryset(self):
        return JobAdvert.objects.prefetch_related("applications", "applications__applicant")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from applications.models import Application
        
        # Application statistics
        applications = self.object.applications.all()
        context['application_count'] = applications.count()
        
        # Recent applications
        context['recent_applications'] = applications.select_related('applicant', 'applicant__applicant_profile').order_by('-submitted_at')[:10]
        
        return context


class JobAdvertCloseView(HRStaffRequiredMixin, DetailView):
    """Close a job advert manually (HR only)."""
    
    model = JobAdvert
    
    def post(self, request, *args, **kwargs):
        job = self.get_object()
        job.status = 'CLOSED'
        job.save()
        messages.success(request, f"Job advert '{job.job_title}' has been closed.")
        log_audit_event(
            actor=request.user,
            action="CLOSE",
            action_description=f"Job advert closed: {job.job_title}",
            entity=job,
            metadata={"job_id": job.job_id, "recruiting_id": job.recruiting_id},
            request=request
        )
        return redirect("management:jobs_management:advert-detail", pk=job.pk)


class JobAdvertReopenView(HRStaffRequiredMixin, DetailView):
    """Reopen a closed job advert manually (HR only)."""
    
    model = JobAdvert
    
    def post(self, request, *args, **kwargs):
        job = self.get_object()
        job.status = 'OPEN'
        job.save()
        messages.success(request, f"Job advert '{job.job_title}' has been reopened.")
        log_audit_event(
            actor=request.user,
            action="REOPEN",
            action_description=f"Job advert reopened: {job.job_title}",
            entity=job,
            metadata={"job_id": job.job_id, "recruiting_id": job.recruiting_id},
            request=request
        )
        return redirect("management:jobs_management:advert-detail", pk=job.pk)


class SkillListView(HRStaffRequiredMixin, ListView):
    """List all skills for HR management."""

    model = Skill
    template_name = "management/jobs/skill_list.html"
    context_object_name = "skills"
    paginate_by = 20

    def get_queryset(self):
        queryset = Skill.objects.all().order_by("name")
        
        # Search by name
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


class SkillCreateView(HRStaffRequiredMixin, CreateView):
    """Create skill (HR only)."""

    model = Skill
    form_class = SkillForm
    template_name = "management/jobs/skill_form.html"
    success_url = reverse_lazy("management:jobs_management:skill-list")

    def form_valid(self, form):
        messages.success(self.request, "Skill created successfully.")
        return super().form_valid(form)


class JobApplicationsListView(HRStaffRequiredMixin, ListView):
    """List all applicants for a specific job."""

    template_name = "management/jobs/applications.html"
    context_object_name = "applications"
    paginate_by = 20

    def get_queryset(self):
        from applications.models import Application
        job = get_object_or_404(JobAdvert, pk=self.kwargs['pk'])
        
        queryset = Application.objects.filter(job_advert=job).select_related("applicant", "applicant__applicant_profile").order_by('-submitted_at')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status in ['SUBMITTED', 'UNDER_REVIEW', 'SHORTLISTED', 'REJECTED']:
            queryset = queryset.filter(status=status)
        
        # Search by applicant name or email
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(applicant__first_name__icontains=search) |
                Q(applicant__last_name__icontains=search) |
                Q(applicant__email__icontains=search)
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        from applications.models import Application
        context = super().get_context_data(**kwargs)
        job = get_object_or_404(JobAdvert, pk=self.kwargs['pk'])
        context['job'] = job
        
        # Application statistics for this job
        applications = Application.objects.filter(job_advert=job)
        context['total_applications'] = applications.count()
        
        # Filters
        context['status_filter'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')
        
        return context


