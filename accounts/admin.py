"""
Admin configuration for accounts app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, OTP, EmployeeProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model."""
    list_display = ['email', 'first_name', 'last_name', 'user_type', 'is_verified', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['user_type', 'is_verified', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('User Type', {'fields': ('user_type',)}),
        ('Permissions', {'fields': ('is_active', 'is_verified', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'user_type', 'is_staff', 'is_superuser'),
        }),
    )
    
    def get_inline_instances(self, request, obj=None):
        """Show EmployeeProfile inline only for employee users."""
        inlines = []
        if obj and obj.user_type == 'EMPLOYEE':
            inline = EmployeeProfileInline(self.model, self.admin_site)
            inlines.append(inline)
        return inlines
    
    def save_model(self, request, obj, form, change):
        """Set is_verified=True for employees and superusers."""
        if obj.user_type == 'EMPLOYEE' or obj.is_superuser:
            obj.is_verified = True
        # If creating a new employee user, ensure they can't self-register
        if obj.user_type == 'EMPLOYEE' and not change:
            obj.is_staff = True  # Employees have staff access
        super().save_model(request, obj, form, change)


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    """Admin interface for OTP model."""
    list_display = ['user', 'code', 'purpose', 'is_used', 'is_expired', 'attempts', 'expires_at', 'created_at']
    list_filter = ['purpose', 'is_used', 'is_expired', 'created_at']
    search_fields = ['user__email', 'code']
    readonly_fields = ['code', 'created_at', 'used_at']
    ordering = ['-created_at']


class EmployeeProfileInline(admin.StackedInline):
    """Inline admin for EmployeeProfile (only for employee users)."""
    model = EmployeeProfile
    extra = 0
    can_delete = False
    fieldsets = (
        ('Employee Information', {
            'fields': ('ec_number', 'phone_number', 'department', 'job_title')
        }),
    )
    
    def get_queryset(self, request):
        """Only show for employee users."""
        qs = super().get_queryset(request)
        return qs.filter(user__user_type='EMPLOYEE')


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    """Admin interface for EmployeeProfile model."""
    list_display = ['ec_number', 'user_email', 'full_name', 'department', 'job_title', 'phone_number', 'created_at']
    list_filter = ['department', 'created_at']
    search_fields = ['ec_number', 'phone_number', 'department', 'job_title', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Employee Information', {
            'fields': ('ec_number', 'phone_number', 'department', 'job_title')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        """Display user email."""
        return obj.user.email
    user_email.short_description = 'Email'
    
    def full_name(self, obj):
        """Display full name."""
        return obj.user.get_full_name()
    full_name.short_description = 'Name'
    
    def save_model(self, request, obj, form, change):
        """Ensure user is set as employee type and verified."""
        if obj.user:
            obj.user.user_type = 'EMPLOYEE'
            obj.user.is_verified = True
            obj.user.is_staff = True  # Employees have staff access
            obj.user.save()
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """Show only employee profiles."""
        qs = super().get_queryset(request)
        return qs.select_related('user').filter(user__user_type='EMPLOYEE')
