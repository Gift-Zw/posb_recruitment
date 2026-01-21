"""
Management views for applications (HR staff only).
Handles viewing and managing all applications.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, View
from django.http import JsonResponse
from jobs.models import JobAdvert
from applications.models import Application, ApplicantProfile
from audit.services import log_audit_event


class HRStaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
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
            return redirect("jobs:list")
        messages.error(self.request, "Employee access required. Please log in with an HR staff account.")
        return redirect("management:login")


class ApplicationManagementListView(HRStaffRequiredMixin, ListView):
    """List all applications for HR management."""

    model = Application
    template_name = "management/applications/list.html"
    context_object_name = "applications"
    paginate_by = 20

    def get_queryset(self):
        queryset = Application.objects.select_related("applicant", "job_advert", "job_advert__category").order_by('-submitted_at')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status in ['SUBMITTED', 'UNDER_REVIEW', 'SHORTLISTED', 'REJECTED']:
            queryset = queryset.filter(status=status)
        
        # Filter by job
        job_id = self.request.GET.get('job_id')
        if job_id:
            queryset = queryset.filter(job_advert_id=job_id)
        
        # Search by applicant name or email
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                applicant__first_name__icontains=search
            ) | queryset.filter(
                applicant__last_name__icontains=search
            ) | queryset.filter(
                applicant__email__icontains=search
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', '')
        context['job_filter'] = self.request.GET.get('job_id', '')
        context['search_query'] = self.request.GET.get('search', '')
        
        # Statistics
        all_applications = Application.objects.all()
        context['total_applications'] = all_applications.count()
        context['submitted_count'] = all_applications.filter(status='SUBMITTED').count()
        context['under_review_count'] = all_applications.filter(status='UNDER_REVIEW').count()
        context['shortlisted_count'] = all_applications.filter(status='SHORTLISTED').count()
        context['rejected_count'] = all_applications.filter(status='REJECTED').count()
        
        # Job list for filter
        context['jobs'] = JobAdvert.objects.all().order_by('-created_at')
        
        return context


class ApplicationManagementDetailView(HRStaffRequiredMixin, DetailView):
    """View application details for HR management."""

    model = Application
    template_name = "management/applications/detail.html"
    context_object_name = "application"

    def get_queryset(self):
        return Application.objects.select_related("applicant", "job_advert", "job_advert__category").prefetch_related("documents")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get current applicant profile (may differ from snapshot)
        try:
            context['current_profile'] = self.object.applicant.applicant_profile
        except ApplicantProfile.DoesNotExist:
            context['current_profile'] = None
        
        return context


class ApplicantProfileManagementView(HRStaffRequiredMixin, DetailView):
    """View full applicant profile for HR management."""

    model = ApplicantProfile
    template_name = "management/applications/applicant_profile.html"
    context_object_name = "profile"

    def get_queryset(self):
        return ApplicantProfile.objects.select_related("user").prefetch_related("skills", "documents")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all applications by this applicant
        context['applications'] = Application.objects.filter(
            applicant=self.object.user
        ).select_related('job_advert', 'job_advert__category').order_by('-submitted_at')
        
        return context


class UpdateApplicationStatusView(HRStaffRequiredMixin, View):
    """Update application status (AJAX or POST)."""

    def post(self, request, *args, **kwargs):
        application = get_object_or_404(Application, pk=kwargs['pk'])
        new_status = request.POST.get('status')
        
        if new_status not in ['SUBMITTED', 'UNDER_REVIEW', 'SHORTLISTED', 'REJECTED']:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)
            messages.error(request, "Invalid status.")
            return redirect('management:applications_management:detail', pk=application.pk)
        
        old_status = application.status
        application.status = new_status
        application.save()
        
        log_audit_event(
            actor=request.user,
            action="APPLICATION_STATUS_UPDATED",
            action_description=f"Application status changed from {old_status} to {new_status}",
            entity=application,
            request=request,
        )
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'status': new_status})
        
        messages.success(request, f"Application status updated to {new_status}.")
        return redirect('management:applications_management:detail', pk=application.pk)
