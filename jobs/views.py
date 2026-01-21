"""
Server-rendered views for jobs app.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Count, Q
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView, FormView
from .models import JobCategory, Skill, JobAdvert
from .forms import JobCategoryForm, SkillForm, JobAdvertForm, ContactForm
from audit.services import log_audit_event


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
        queryset = (
            JobAdvert.objects.select_related("category")
            .prefetch_related("required_skills")
            .filter(status="OPEN")
            .order_by("-created_at")
        )
        
        # Search by title
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(title__icontains=search)
        
        # Filter by category (multiple allowed)
        categories = self.request.GET.getlist('category')
        if categories:
            queryset = queryset.filter(category_id__in=categories)
        
        # Filter by location/city (multiple allowed)
        locations = self.request.GET.getlist('location')
        if locations:
            queryset = queryset.filter(location__in=locations)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get categories with open job counts (only show categories that have open jobs)
        context['categories'] = JobCategory.objects.annotate(
            job_count=Count('job_adverts', filter=Q(job_adverts__status='OPEN'))
        ).filter(job_count__gt=0).order_by('name')
        
        context['selected_categories'] = self.request.GET.getlist('category')
        
        # Get distinct locations from open jobs with counts
        location_counts = JobAdvert.objects.filter(status='OPEN').exclude(location='').values('location').annotate(
            job_count=Count('id')
        ).order_by('location')
        context['locations'] = location_counts
        context['selected_locations'] = self.request.GET.getlist('location')
        return context


class JobDetailView(DetailView):
    """Job detail view."""

    model = JobAdvert
    template_name = "jobs/detail.html"
    context_object_name = "job"

    def get_queryset(self):
        qs = JobAdvert.objects.select_related("category").prefetch_related("required_skills")
        if not self.request.user.is_authenticated or (not self.request.user.is_employee() and not self.request.user.is_superuser):
            qs = qs.filter(status="OPEN")
        return qs


class ManagementDashboardView(HRStaffRequiredMixin, TemplateView):
    """Management dashboard with statistics and overview."""

    template_name = "management/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from applications.models import Application
        
        # Job statistics
        context['total_jobs'] = JobAdvert.objects.count()
        context['open_jobs'] = JobAdvert.objects.filter(status='OPEN').count()
        context['draft_jobs'] = JobAdvert.objects.filter(status='DRAFT').count()
        context['closed_jobs'] = JobAdvert.objects.filter(status='CLOSED').count()
        
        # Application statistics
        context['total_applications'] = Application.objects.count()
        context['submitted_applications'] = Application.objects.filter(status='SUBMITTED').count()
        context['under_review_applications'] = Application.objects.filter(status='UNDER_REVIEW').count()
        context['shortlisted_applications'] = Application.objects.filter(status='SHORTLISTED').count()
        context['rejected_applications'] = Application.objects.filter(status='REJECTED').count()
        
        # Recent job adverts
        context['recent_jobs'] = JobAdvert.objects.select_related('category', 'created_by').prefetch_related('applications').order_by('-created_at')[:5]
        
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
        
        queryset = JobAdvert.objects.select_related("category", "created_by").prefetch_related("required_skills").annotate(
            application_count=Count('applications'),
            shortlisted_count=Count('applications', filter=Q(applications__status='SHORTLISTED'))
        ).order_by("-created_at")
        
        # Filter by status
        status = self.request.GET.get('status')
        if status in ['DRAFT', 'OPEN', 'CLOSED']:
            queryset = queryset.filter(status=status)
        
        # Search by title or category
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(title__icontains=search)
        
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
        return JobAdvert.objects.select_related("category", "created_by").prefetch_related("required_skills", "applications", "applications__applicant")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from applications.models import Application
        
        # Application statistics
        applications = self.object.applications.all()
        context['application_count'] = applications.count()
        context['submitted_count'] = applications.filter(status='SUBMITTED').count()
        context['under_review_count'] = applications.filter(status='UNDER_REVIEW').count()
        context['shortlisted_count'] = applications.filter(status='SHORTLISTED').count()
        context['rejected_count'] = applications.filter(status='REJECTED').count()
        
        # Recent applications
        context['recent_applications'] = applications.select_related('applicant').order_by('-submitted_at')[:10]
        
        return context


class JobAdvertCreateView(HRStaffRequiredMixin, CreateView):
    """Create job advert (HR only)."""

    model = JobAdvert
    form_class = JobAdvertForm
    template_name = "management/jobs/advert_form.html"
    success_url = reverse_lazy("management:jobs_management:list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Job advert created.")
        log_audit_event(
            actor=self.request.user,
            action="CREATE",
            action_description=f"Job advert created: {form.instance.title}",
            entity=form.instance,
            metadata={"title": form.instance.title},
            request=self.request
        )
        return response


class JobAdvertUpdateView(HRStaffRequiredMixin, UpdateView):
    """Update job advert (HR only)."""

    model = JobAdvert
    form_class = JobAdvertForm
    template_name = "management/jobs/advert_form.html"
    success_url = reverse_lazy("management:jobs_management:list")

    def form_valid(self, form):
        messages.success(self.request, "Job advert updated.")
        log_audit_event(
            actor=self.request.user,
            action="UPDATE",
            action_description=f"Job advert updated: {form.instance.title}",
            entity=form.instance,
            metadata={"title": form.instance.title},
            request=self.request
        )
        return super().form_valid(form)


class JobCategoryListView(HRStaffRequiredMixin, ListView):
    """List all job categories for HR management."""

    model = JobCategory
    template_name = "management/jobs/category_list.html"
    context_object_name = "categories"
    paginate_by = 20

    def get_queryset(self):
        queryset = JobCategory.objects.all().order_by("name")
        
        # Search by name
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


class JobCategoryCreateView(HRStaffRequiredMixin, CreateView):
    """Create job category (HR only)."""

    model = JobCategory
    form_class = JobCategoryForm
    template_name = "management/jobs/category_form.html"
    success_url = reverse_lazy("management:jobs_management:category-list")

    def form_valid(self, form):
        messages.success(self.request, "Category created successfully.")
        return super().form_valid(form)


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
