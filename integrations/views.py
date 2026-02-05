"""
Server-rendered views for ERP export triggers (HR only).
"""
import secrets
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import ListView, CreateView, DetailView
from django.urls import reverse_lazy
from django.db.models import Q, Count
from integrations.models import ERPExport, APIKey
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
        messages.success(request, f"ERP export triggered for {run.job_advert.job_title}.")
        return redirect("management:integrations_management:exports")

    def get(self, request, *args, **kwargs):
        return redirect("management:integrations_management:exports")


class APIKeyListView(HRStaffRequiredMixin, ListView):
    """List all API keys."""

    model = APIKey
    template_name = "management/integrations/api_keys.html"
    context_object_name = "api_keys"
    paginate_by = 20

    def get_queryset(self):
        queryset = APIKey.objects.select_related('created_by').order_by('-created_at')
        
        # Filter by active status
        is_active = self.request.GET.get('is_active')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)
        
        # Search by name
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['is_active_filter'] = self.request.GET.get('is_active', '')
        context['total_keys'] = APIKey.objects.count()
        context['active_keys'] = APIKey.objects.filter(is_active=True).count()
        context['inactive_keys'] = APIKey.objects.filter(is_active=False).count()
        return context


class APIKeyCreateView(HRStaffRequiredMixin, CreateView):
    """Create a new API key."""

    model = APIKey
    template_name = "management/integrations/api_key_form.html"
    fields = ['name', 'is_active']

    def form_valid(self, form):
        # Generate secure API key
        form.instance.key = secrets.token_urlsafe(32)
        form.instance.created_by = self.request.user
        form.save()
        # Store the key in context to display it
        self.new_key = {
            'name': form.instance.name,
            'key': form.instance.key
        }
        messages.success(self.request, f"API key '{form.instance.name}' created successfully!")
        return self.render_to_response(self.get_context_data(form=form, new_key=self.new_key))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'new_key' in kwargs:
            context['new_key'] = kwargs['new_key']
        else:
            context['new_key'] = None
        return context


class APIKeyToggleView(HRStaffRequiredMixin, DetailView):
    """Toggle API key active status."""

    model = APIKey

    def post(self, request, *args, **kwargs):
        api_key = self.get_object()
        api_key.is_active = not api_key.is_active
        api_key.save()
        status = "activated" if api_key.is_active else "deactivated"
        messages.success(request, f"API key '{api_key.name}' has been {status}.")
        return redirect("management:integrations_management:api-keys")


