"""
Management views for user management (HR staff only).
Handles creating, editing, and managing user accounts.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, View
from django.contrib.auth import get_user_model
from .models import EmployeeProfile
from .forms import UserCreateForm, UserUpdateForm
from audit.services import log_audit_event

User = get_user_model()


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


class EmployeeManagementListView(HRStaffRequiredMixin, ListView):
    """List all employees for HR management."""

    model = User
    template_name = "management/users/employees.html"
    context_object_name = "employees"
    paginate_by = 20

    def get_queryset(self):
        queryset = User.objects.filter(user_type='EMPLOYEE').select_related('employee_profile').order_by('-date_joined')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        # Search by name or email
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                email__icontains=search
            ) | queryset.filter(
                first_name__icontains=search
            ) | queryset.filter(
                last_name__icontains=search
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')
        
        # Statistics for employees only
        employees = User.objects.filter(user_type='EMPLOYEE')
        context['total_employees'] = employees.count()
        context['active_employees'] = employees.filter(is_active=True).count()
        context['inactive_employees'] = employees.filter(is_active=False).count()
        
        return context


class ApplicantManagementListView(HRStaffRequiredMixin, ListView):
    """List all applicants for HR management."""

    model = User
    template_name = "management/users/applicants.html"
    context_object_name = "applicants"
    paginate_by = 20

    def get_queryset(self):
        queryset = User.objects.filter(user_type='APPLICANT').order_by('-date_joined')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        elif status == 'verified':
            queryset = queryset.filter(is_verified=True)
        elif status == 'unverified':
            queryset = queryset.filter(is_verified=False)
        
        # Search by name or email
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                email__icontains=search
            ) | queryset.filter(
                first_name__icontains=search
            ) | queryset.filter(
                last_name__icontains=search
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')
        
        # Statistics for applicants only
        applicants = User.objects.filter(user_type='APPLICANT')
        context['total_applicants'] = applicants.count()
        context['active_applicants'] = applicants.filter(is_active=True).count()
        context['inactive_applicants'] = applicants.filter(is_active=False).count()
        context['verified_applicants'] = applicants.filter(is_verified=True).count()
        context['unverified_applicants'] = applicants.filter(is_verified=False).count()
        
        return context


class UserManagementCreateView(HRStaffRequiredMixin, CreateView):
    """Create new employee/staff user."""

    model = User
    form_class = UserCreateForm
    template_name = "management/users/form.html"
    success_url = reverse_lazy("management:users_management:employees")

    def form_valid(self, form):
        user = form.save(commit=False)
        user.user_type = 'EMPLOYEE'  # All users created here are employees
        user.is_verified = True  # Employees bypass OTP
        user.is_staff = True  # Employees have staff access
        user.is_active = form.cleaned_data.get('is_active', True)
        user.set_password(form.cleaned_data['password'])
        user.save()
        
        # Create employee profile if EC number or phone provided
        ec_number = form.cleaned_data.get('ec_number')
        phone_number = form.cleaned_data.get('phone_number')
        department = form.cleaned_data.get('department')
        job_title = form.cleaned_data.get('job_title')
        
        if ec_number or phone_number or department or job_title:
            EmployeeProfile.objects.create(
                user=user,
                ec_number=ec_number,
                phone_number=phone_number,
                department=department,
                job_title=job_title
            )
        
        log_audit_event(
            actor=self.request.user,
            action="USER_CREATED",
            action_description=f"HR staff created new employee: {user.email}",
            entity=user,
            request=self.request,
        )
        
        messages.success(self.request, f"Employee account created successfully for {user.email}.")
        return super().form_valid(form)


class UserManagementUpdateView(HRStaffRequiredMixin, UpdateView):
    """Update user account."""

    model = User
    form_class = UserUpdateForm
    template_name = "management/users/form.html"
    success_url = reverse_lazy("management:users_management:employees")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get or create employee profile
        context['employee_profile'] = getattr(self.object, 'employee_profile', None)
        return context

    def form_valid(self, form):
        user = form.save(commit=False)
        
        # Update password if provided
        password = form.cleaned_data.get('password')
        if password:
            user.set_password(password)
        
        user.save()
        
        # Update or create employee profile
        if user.user_type == 'EMPLOYEE':
            profile, created = EmployeeProfile.objects.get_or_create(user=user)
            profile.ec_number = form.cleaned_data.get('ec_number', '')
            profile.phone_number = form.cleaned_data.get('phone_number', '')
            profile.department = form.cleaned_data.get('department', '')
            profile.job_title = form.cleaned_data.get('job_title', '')
            profile.save()
        
        log_audit_event(
            actor=self.request.user,
            action="USER_UPDATED",
            action_description=f"HR staff updated user: {user.email}",
            entity=user,
            request=self.request,
        )
        
        messages.success(self.request, f"User account updated successfully.")
        
        # Redirect based on user type
        if user.user_type == 'EMPLOYEE':
            self.success_url = reverse_lazy("management:users_management:employees")
        else:
            self.success_url = reverse_lazy("management:users_management:applicants")
        
        return super().form_valid(form)


class ToggleUserStatusView(HRStaffRequiredMixin, View):
    """Toggle user active/inactive status."""

    def post(self, request, *args, **kwargs):
        user = get_object_or_404(User, pk=kwargs['pk'])
        
        # Prevent deactivating yourself
        if user == request.user:
            messages.error(request, "You cannot deactivate your own account.")
            if user.user_type == 'EMPLOYEE':
                return redirect('management:users_management:employees')
            else:
                return redirect('management:users_management:applicants')
        
        old_status = user.is_active
        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])
        
        status_text = "activated" if user.is_active else "deactivated"
        log_audit_event(
            actor=request.user,
            action="USER_STATUS_TOGGLED",
            action_description=f"User {user.email} {status_text}",
            entity=user,
            request=request,
        )
        
        messages.success(request, f"User {user.email} has been {status_text}.")
        if user.user_type == 'EMPLOYEE':
            return redirect('management:users_management:employees')
        else:
            return redirect('management:users_management:applicants')
