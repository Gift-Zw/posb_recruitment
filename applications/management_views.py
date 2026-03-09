"""
Management views for applications (HR staff only).
Handles viewing and managing all applications.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import ListView, DetailView, View
from jobs.models import JobAdvert
from applications.models import Application, ApplicantProfile


def apply_application_filters(queryset, status=None, job_id=None, search=None):
    """Apply reusable status/job/search filters to application querysets."""
    if status in ['PENDING_UPLOAD', 'UPLOADED_TO_ERP', 'UPLOAD_FAILED']:
        queryset = queryset.filter(status=status)

    if job_id:
        queryset = queryset.filter(job_advert_id=job_id)

    if search:
        queryset = queryset.filter(
            Q(applicant__first_name__icontains=search) |
            Q(applicant__last_name__icontains=search) |
            Q(applicant__email__icontains=search)
        )

    return queryset


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
        queryset = Application.objects.select_related("applicant", "job_advert").order_by('-submitted_at')
        queryset = apply_application_filters(
            queryset,
            status=self.request.GET.get('status'),
            job_id=self.request.GET.get('job_id'),
            search=self.request.GET.get('search'),
        )
        review_status = self.request.GET.get('review_status')
        if review_status in ['PENDING_REVIEW', 'APPROVED', 'REJECTED']:
            queryset = queryset.filter(review_status=review_status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', '')
        context['job_filter'] = self.request.GET.get('job_id', '')
        context['search_query'] = self.request.GET.get('search', '')
        
        # Statistics
        all_applications = Application.objects.all()
        context['total_applications'] = all_applications.count()
        context['pending_upload_count'] = all_applications.filter(status='PENDING_UPLOAD').count()
        context['uploaded_to_erp_count'] = all_applications.filter(status='UPLOADED_TO_ERP').count()
        context['upload_failed_count'] = all_applications.filter(status='UPLOAD_FAILED').count()
        context['pending_review_count'] = all_applications.filter(review_status='PENDING_REVIEW').count()
        context['approved_count'] = all_applications.filter(review_status='APPROVED').count()
        context['rejected_count'] = all_applications.filter(review_status='REJECTED').count()
        context['review_status_filter'] = self.request.GET.get('review_status', '')
        
        # Job list for filter
        context['jobs'] = JobAdvert.objects.all().order_by('-created_at')
        
        return context


class ApplicationManagementDetailView(HRStaffRequiredMixin, DetailView):
    """View application details for HR management."""

    model = Application
    template_name = "management/applications/detail.html"
    context_object_name = "application"

    def get_queryset(self):
        return Application.objects.select_related("applicant", "job_advert").prefetch_related("documents")

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
        return ApplicantProfile.objects.select_related("user").prefetch_related("documents")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all applications by this applicant
        context['applications'] = Application.objects.filter(
            applicant=self.object.user
        ).select_related('job_advert').order_by('-submitted_at')
        
        return context


class UploadSingleApplicationView(HRStaffRequiredMixin, View):
    """Queue a single application ERP upload."""

    def post(self, request, *args, **kwargs):
        application = get_object_or_404(Application, pk=kwargs['pk'])
        next_url = request.POST.get("next")

        if application.status == "UPLOADED_TO_ERP":
            messages.info(request, "This application is already uploaded to ERP.")
            if next_url:
                return redirect(next_url)
            return redirect('management:applications_management:detail', pk=application.pk)

        if application.review_status != "APPROVED":
            messages.error(request, "Only approved applications can be pushed to D365.")
            if next_url:
                return redirect(next_url)
            return redirect('management:applications_management:detail', pk=application.pk)

        from integrations.tasks import enqueue_push_application_to_d365_task
        queued = enqueue_push_application_to_d365_task(application.id)
        if queued:
            messages.success(request, "ERP upload started in the background.")
        else:
            messages.error(request, "Could not start ERP upload. Check system logs.")

        if next_url:
            return redirect(next_url)
        return redirect('management:applications_management:detail', pk=application.pk)


class UploadBulkApplicationsView(HRStaffRequiredMixin, View):
    """Queue ERP uploads in bulk based on current filters."""

    def post(self, request, *args, **kwargs):
        queryset = Application.objects.select_related("job_advert")
        queryset = apply_application_filters(
            queryset,
            status=request.POST.get("status"),
            job_id=request.POST.get("job_id"),
            search=request.POST.get("search"),
        )
        review_status = request.POST.get("review_status")
        if review_status in ['PENDING_REVIEW', 'APPROVED', 'REJECTED']:
            queryset = queryset.filter(review_status=review_status)
        else:
            queryset = queryset.filter(review_status="APPROVED")
        queryset = queryset.filter(status__in=["PENDING_UPLOAD", "UPLOAD_FAILED"])

        job_ids = list(queryset.values_list("job_advert_id", flat=True).distinct())
        if not job_ids:
            messages.info(request, "No approved pending/failed applications found for bulk upload.")
            return redirect('management:applications_management:list')

        from integrations.tasks import enqueue_push_all_applications_for_job_task
        started = 0
        for job_id in job_ids:
            if enqueue_push_all_applications_for_job_task(job_id, triggered_by_id=request.user.id):
                started += 1

        if started:
            messages.success(request, f"Started background bulk upload for {started} job advert(s).")
        else:
            messages.error(request, "Could not start any bulk uploads. Check system logs.")

        return redirect('management:applications_management:list')


class ReviewSingleApplicationView(HRStaffRequiredMixin, View):
    """Approve or reject a single application from application detail view."""

    def post(self, request, *args, **kwargs):
        application = get_object_or_404(Application, pk=kwargs['pk'])
        action = request.POST.get("action")
        next_url = request.POST.get("next")

        if action not in {"approve", "reject"}:
            messages.error(request, "Invalid review action.")
            if next_url:
                return redirect(next_url)
            return redirect('management:applications_management:detail', pk=application.pk)
        if application.status == "UPLOADED_TO_ERP":
            messages.info(request, "This application is already uploaded to D365 and cannot be re-reviewed.")
            if next_url:
                return redirect(next_url)
            return redirect('management:applications_management:detail', pk=application.pk)

        application.reviewed_by = request.user
        application.reviewed_at = timezone.now()

        if action == "approve":
            application.review_status = "APPROVED"
            application.save(update_fields=["review_status", "reviewed_by", "reviewed_at", "updated_at"])
            from integrations.tasks import enqueue_push_application_to_d365_task
            enqueue_push_application_to_d365_task(application.id)
            messages.success(request, "Application approved and queued for D365 push.")
        else:
            application.review_status = "REJECTED"
            application.save(update_fields=["review_status", "reviewed_by", "reviewed_at", "updated_at"])
            messages.success(request, "Application rejected.")

        log_audit_event(
            actor=request.user,
            action="APPLICATION_UPDATED",
            action_description=f"Application {application.id} marked as {application.review_status}",
            entity=application,
            metadata={"review_status": application.review_status},
            request=request,
        )

        if next_url:
            return redirect(next_url)
        return redirect('management:applications_management:detail', pk=application.pk)
