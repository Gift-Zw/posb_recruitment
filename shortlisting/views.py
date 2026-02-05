"""
Server-rendered views for shortlisting management (HR only).
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView
from jobs.models import JobAdvert
from shortlisting.models import ShortlistingRun
from shortlisting.tasks import trigger_shortlisting_task


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


class ShortlistingRunListView(HRStaffRequiredMixin, ListView):
    """List shortlisting runs for HR visibility."""

    model = ShortlistingRun
    template_name = "management/shortlisting/list.html"
    context_object_name = "runs"
    paginate_by = 20

    def get_queryset(self):
        return ShortlistingRun.objects.select_related("job_advert", "triggered_by")


class TriggerShortlistingView(HRStaffRequiredMixin, ListView):
    """
    Trigger shortlisting for a job advert.
    Uses Celery task to run asynchronously.
    """

    template_name = "shortlisting/trigger.html"

    def post(self, request, *args, **kwargs):
        job = get_object_or_404(JobAdvert, pk=kwargs["job_id"])
        trigger_shortlisting_task(job.id, triggered_by_id=request.user.id, trigger_type="MANUAL")
        messages.success(request, f"Shortlisting triggered for {job.job_title}.")
        return redirect("management:shortlisting_management:list")

    def get(self, request, *args, **kwargs):
        # Redirect to list; no GET form needed
        return redirect("management:shortlisting_management:list")
