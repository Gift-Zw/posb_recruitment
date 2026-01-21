"""
Server-rendered views for ERP export triggers (HR only).
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import ListView
from integrations.models import ERPExport
from shortlisting.models import ShortlistingRun
from integrations.tasks import export_to_erp_task


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


class ERPExportListView(HRStaffRequiredMixin, ListView):
    """List ERP exports."""

    model = ERPExport
    template_name = "management/integrations/exports.html"
    context_object_name = "exports"
    paginate_by = 20

    def get_queryset(self):
        return ERPExport.objects.select_related("job_advert", "shortlisting_run")


class TriggerExportView(HRStaffRequiredMixin, ListView):
    """Trigger ERP export for a given shortlisting run."""

    template_name = "integrations/trigger.html"

    def post(self, request, *args, **kwargs):
        run = get_object_or_404(ShortlistingRun, pk=kwargs["run_id"])
        export_to_erp_task(run.id, triggered_by_id=request.user.id)
        messages.success(request, f"ERP export triggered for {run.job_advert.title}.")
        return redirect("management:integrations_management:exports")

    def get(self, request, *args, **kwargs):
        return redirect("management:integrations_management:exports")
