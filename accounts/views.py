"""
Template-based views for accounts app.
"""
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.shortcuts import redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.generic import FormView, UpdateView, TemplateView
from django.contrib.auth import update_session_auth_hash
from django.conf import settings
from .models import User
from .forms import (
    RegistrationForm,
    OTPRequestForm,
    OTPVerifyForm,
    LoginForm,
    ManagementLoginForm,
    ProfileForm,
    ApplicantProfileForm,
    PasswordChangeForm,
    PasswordResetRequestForm,
    PasswordResetConfirmForm,
)
from .services import UserService, OTPService
from audit.services import log_audit_event
from system_logs.services import log_system_event


class RegistrationView(FormView):
    """Register a new applicant and send OTP."""

    template_name = "accounts/register.html"
    form_class = RegistrationForm
    success_url = reverse_lazy("otp-verify")

    def form_valid(self, form):
        user, _, error = UserService.register_user(
            email=form.cleaned_data["email"],
            password=form.cleaned_data["password1"],
            first_name=form.cleaned_data.get("first_name", ""),
            last_name=form.cleaned_data.get("last_name", ""),
        )
        if error:
            messages.error(self.request, error)
            return self.form_invalid(form)
        
        # Store email in session for OTP verification
        self.request.session['registration_email'] = form.cleaned_data["email"]
        
        messages.success(
            self.request,
            "Registration successful. Please check your email for the OTP.",
        )
        return super().form_valid(form)


class OTPRequestView(FormView):
    """Request a new OTP."""

    template_name = "accounts/otp_request.html"
    form_class = OTPRequestForm
    success_url = reverse_lazy("otp-verify")

    def form_valid(self, form):
        try:
            user = User.objects.get(email=form.cleaned_data["email"])
            purpose = form.cleaned_data.get("purpose") or "email_verification"
            OTPService.generate_otp(user, purpose=purpose)
            messages.success(self.request, "OTP sent. Please check your email.")
        except User.DoesNotExist:
            messages.error(self.request, "User with this email does not exist.")
        return super().form_valid(form)


class OTPVerifyView(FormView):
    """Verify OTP and activate account."""

    template_name = "accounts/otp_verify.html"
    form_class = OTPVerifyForm
    success_url = reverse_lazy("jobs:list")

    def get_initial(self):
        """Pre-fill email from session if available."""
        initial = super().get_initial()
        if 'registration_email' in self.request.session:
            initial['email'] = self.request.session['registration_email']
        return initial

    def form_valid(self, form):
        try:
            email = form.cleaned_data["email"]
            user = User.objects.get(email=email)
            purpose = form.cleaned_data.get("purpose") or "email_verification"
            success, message, _ = OTPService.verify_otp(
                user, form.cleaned_data["code"], purpose=purpose
            )
            if success:
                # Clear registration email from session
                if 'registration_email' in self.request.session:
                    del self.request.session['registration_email']
                login(self.request, user)
                messages.success(self.request, "Account verified and logged in.")
                log_audit_event(
                    actor=user,
                    action="OTP_VERIFICATION",
                    action_description="OTP verified via web form",
                    request=self.request,
                )
                return super().form_valid(form)
            messages.error(self.request, message)
        except User.DoesNotExist:
            messages.error(self.request, "User with this email does not exist.")
        return redirect("otp-verify")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get email from session or form initial
        email = self.request.session.get('registration_email', '')
        if email:
            context['user_email'] = email
            # Mask email for display: first char + *** + @ + domain
            if '@' in email:
                email_parts = email.split('@')
                context['masked_email'] = f"{email_parts[0][:1]}***@{email_parts[1]}"
            else:
                context['masked_email'] = f"{email[:1]}***@{email[-10:]}"
        return context


class LoginView(FormView):
    """Session-based login."""

    template_name = "accounts/login.html"
    form_class = LoginForm
    success_url = reverse_lazy("jobs:list")

    def form_valid(self, form):
        user = form.cleaned_data["user"]
        needs_verification = form.cleaned_data.get("needs_verification", False)
        
        # If user needs verification, generate OTP and redirect to OTP verification
        if needs_verification:
            # Generate OTP for the user (email sending happens in background thread)
            from .services import OTPService
            OTPService.generate_otp(user, purpose='email_verification')
            
            # Store email in session for OTP verification
            self.request.session['registration_email'] = user.email
            messages.info(self.request, "Please verify your email address to continue. A verification code has been sent to your email.")
            return redirect("otp-verify")
        
        # User is verified, proceed with login
        login(self.request, user)
        log_audit_event(
            actor=user,
            action="LOGIN",
            action_description=f"User logged in: {user.email}",
            request=self.request,
        )
        
        # Redirect employees and superusers to management portal
        if user.is_employee() or user.is_superuser:
            return redirect("management:dashboard")
        
        return super().form_valid(form)


class ManagementLoginView(FormView):
    """Management portal login (HR employees only)."""

    template_name = "management/login.html"
    form_class = ManagementLoginForm
    success_url = reverse_lazy("management:dashboard")

    def dispatch(self, request, *args, **kwargs):
        # If already logged in as employee or superuser, redirect to management portal
        if request.user.is_authenticated and (request.user.is_employee() or request.user.is_superuser):
            return redirect("management:dashboard")
        # If logged in as applicant, redirect to public portal
        if request.user.is_authenticated and request.user.is_applicant():
            messages.warning(request, "This login is for HR staff only. You are logged in as an applicant.")
            return redirect("jobs:list")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.cleaned_data["user"]
        
        # Double-check: only employees and superusers should reach here (form validation should catch this)
        if not user.is_employee() and not user.is_superuser:
            messages.error(self.request, "This login is for HR staff only.")
            return redirect("home")
        
        # Log in the user
        login(self.request, user)
        log_audit_event(
            actor=user,
            action="MANAGEMENT_LOGIN",
            action_description=f"HR staff logged into management portal: {user.email}",
            request=self.request,
        )
        return super().form_valid(form)


class LogoutView(TemplateView):
    """Logout view with user-type based redirect."""

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            # Store user type and reference before logout (since user won't be available after)
            user = request.user
            is_employee = user.is_employee() or user.is_superuser
            
            # Log the logout event before logging out (so we have the actor)
            log_audit_event(
                actor=user,
                action="LOGOUT",
                action_description=f"User logged out: {user.email}",
                request=request,
            )
            
            # Now logout
            logout(request)
            messages.info(request, "You have been logged out.")
            
            # Redirect based on user type
            if is_employee:
                return redirect("management:login")
            else:
                return redirect("home")
        
        # If not authenticated, redirect to home
        return redirect("home")


class ProfileView(LoginRequiredMixin, TemplateView):
    """Comprehensive profile management view with multiple sections."""

    template_name = "accounts/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        active_tab = self.request.GET.get('tab', 'personal')
        allowed_tabs = {'personal', 'documents', 'password'}
        if active_tab not in allowed_tabs:
            active_tab = 'personal'
        
        # Get or create applicant profile if user is an applicant
        applicant_profile = None
        if user.is_applicant():
            from applications.models import ApplicantProfile
            applicant_profile, _ = ApplicantProfile.objects.get_or_create(user=user)
        
        # Initialize forms
        context['user_form'] = ProfileForm(instance=user, prefix='user')
        context['password_form'] = PasswordChangeForm(user=user, prefix='password')
        context['active_tab'] = active_tab
        
        if applicant_profile:
            context['applicant_profile'] = applicant_profile
            context['applicant_form'] = ApplicantProfileForm(instance=applicant_profile, prefix='applicant')
            # Get countries for selectors
            from jobs.models import Country
            context['all_countries'] = Country.objects.filter(is_active=True).order_by('sort_order', 'name')
            
            # Calculate profile completion percentage
            completion = 0
            total_fields = 3  # personal, contact, documents
            if user.first_name and user.last_name and applicant_profile.phone_number:
                completion += 1  # Personal info
            if applicant_profile.address_line_1 and applicant_profile.city and applicant_profile.country_id:
                completion += 1  # Contact
            # Documents - check if user has uploaded any documents
            from applications.models import ApplicantProfileDocument
            if ApplicantProfileDocument.objects.filter(applicant_profile=applicant_profile).exists():
                completion += 1  # Documents
            
            # Get uploaded documents for display
            context['uploaded_documents'] = ApplicantProfileDocument.objects.filter(
                applicant_profile=applicant_profile
            ).order_by('-uploaded_at')
            from applications.forms import DocumentUploadForm
            context['document_form'] = DocumentUploadForm()
            
            context['profile_completion'] = int((completion / total_fields) * 100)
            context['profile_completion_message'] = self._get_completion_message(completion, total_fields)
        else:
            context['applicant_form'] = None
            context['uploaded_documents'] = []
            from applications.forms import DocumentUploadForm
            context['document_form'] = DocumentUploadForm()
            context['profile_completion'] = 0
            context['profile_completion_message'] = "Complete your profile to get started"
        
        return context
    
    def _get_completion_message(self, completion, total_fields):
        """Get a helpful message about what to complete next."""
        if completion == total_fields:
            return "Your profile is complete!"
        elif completion == 0:
            return "Complete your personal information to get started"
        elif completion == 1:
            return "Add your contact information to continue"
        elif completion == 2:
            return "Upload your documents to complete your profile"
        return "Complete your profile to reach 100%"

    def post(self, request, *args, **kwargs):
        user = request.user
        active_tab = request.POST.get('active_tab', 'personal')
        
        # Handle different form submissions based on active tab
        if 'user_submit' in request.POST:
            form = ProfileForm(request.POST, instance=user, prefix='user')
            if form.is_valid():
                form.save()
                # If applicant_submit is also present, handle it too and show only one message
                if 'applicant_submit' in request.POST and user.is_applicant():
                    from applications.models import ApplicantProfile
                    applicant_profile, _ = ApplicantProfile.objects.get_or_create(user=user)
                    applicant_form = ApplicantProfileForm(request.POST, instance=applicant_profile, prefix='applicant')
                    if applicant_form.is_valid():
                        profile = applicant_form.save(commit=False)
                        profile.save()
                        messages.success(request, "Profile information updated successfully.")
                        log_audit_event(
                            actor=user,
                            action="APPLICANT_PROFILE_UPDATED",
                            action_description="Applicant profile updated",
                            entity=applicant_profile,
                            request=request,
                        )
                    else:
                        # If applicant form is invalid, still show user form success
                        messages.success(request, "Basic information updated successfully.")
                        log_audit_event(
                            actor=user,
                            action="PROFILE_UPDATED",
                            action_description="User basic information updated",
                            entity=user,
                            request=request,
                        )
                else:
                    # Only user form was submitted
                    messages.success(request, "Basic information updated successfully.")
                    log_audit_event(
                        actor=user,
                        action="PROFILE_UPDATED",
                        action_description="User basic information updated",
                        entity=user,
                        request=request,
                    )
                return redirect(f"{reverse_lazy('applicant-profile')}?tab=personal")
            else:
                # If form is invalid, also try to save applicant profile if present
                if 'applicant_submit' in request.POST and user.is_applicant():
                    from applications.models import ApplicantProfile
                    applicant_profile, _ = ApplicantProfile.objects.get_or_create(user=user)
                    applicant_form = ApplicantProfileForm(request.POST, instance=applicant_profile, prefix='applicant')
                    if applicant_form.is_valid():
                        profile = applicant_form.save(commit=False)
                        profile.save()
                        messages.success(request, "Profile information updated successfully.")
        
        elif 'password_submit' in request.POST:
            form = PasswordChangeForm(user=user, data=request.POST, prefix='password')
            if form.is_valid():
                user.set_password(form.cleaned_data['new_password1'])
                user.save()
                update_session_auth_hash(request, user)  # Keep user logged in
                messages.success(request, "Password changed successfully.")
                log_audit_event(
                    actor=user,
                    action="PASSWORD_CHANGED",
                    action_description="User password changed via profile",
                    request=request,
                )
                return redirect(f"{reverse_lazy('applicant-profile')}?tab=password")
        
        elif 'applicant_submit' in request.POST and user.is_applicant():
            from applications.models import ApplicantProfile
            applicant_profile, _ = ApplicantProfile.objects.get_or_create(user=user)
            form = ApplicantProfileForm(request.POST, instance=applicant_profile, prefix='applicant')
            if form.is_valid():
                profile = form.save(commit=False)
                profile.save()
                messages.success(request, "Profile information updated successfully.")
                log_audit_event(
                    actor=user,
                    action="APPLICANT_PROFILE_UPDATED",
                    action_description="Applicant profile updated",
                    entity=applicant_profile,
                    request=request,
                )
                # Determine redirect tab based on which form was submitted
                redirect_tab = active_tab if active_tab else 'personal'
                return redirect(f"{reverse_lazy('applicant-profile')}?tab={redirect_tab}")
        
        elif 'document_upload' in request.POST and user.is_applicant():
            from applications.models import ApplicantProfile
            from applications.forms import DocumentUploadForm
            applicant_profile, _ = ApplicantProfile.objects.get_or_create(user=user)
            form = DocumentUploadForm(request.POST, request.FILES)
            if form.is_valid():
                document = form.save(commit=False)
                document.applicant_profile = applicant_profile
                if request.FILES.get('file'):
                    document.file_name = request.FILES['file'].name
                    document.file_size = request.FILES['file'].size
                document.save()
                messages.success(request, f"Document '{document.file_name}' uploaded successfully.")
                log_audit_event(
                    actor=user,
                    action="DOCUMENT_UPLOADED",
                    action_description=f"Document uploaded: {document.document_type} - {document.file_name}",
                    entity=document,
                    request=request,
                )
                return redirect(f"{reverse_lazy('applicant-profile')}?tab=documents")
            else:
                # Re-render with form errors
                context = self.get_context_data()
                context['document_form'] = form
                messages.error(request, "Please correct the errors below.")
                return self.render_to_response(context)
        
        elif 'document_delete' in request.POST and user.is_applicant():
            from applications.models import ApplicantProfile, ApplicantProfileDocument
            document_id = request.POST.get('document_id')
            try:
                document = ApplicantProfileDocument.objects.get(
                    id=document_id,
                    applicant_profile__user=user
                )
                document_name = document.file_name
                document.delete()
                messages.success(request, f"Document '{document_name}' deleted successfully.")
                log_audit_event(
                    actor=user,
                    action="DOCUMENT_DELETED",
                    action_description=f"Document deleted: {document_name}",
                    request=request,
                )
                return redirect(f"{reverse_lazy('applicant-profile')}?tab=documents")
            except ApplicantProfileDocument.DoesNotExist:
                messages.error(request, "Document not found.")
                return redirect(f"{reverse_lazy('applicant-profile')}?tab=documents")
        
        # If form is invalid, re-render with errors
        context = self.get_context_data()
        if 'user_submit' in request.POST:
            context['user_form'] = form
        elif 'password_submit' in request.POST:
            context['password_form'] = form
        elif 'applicant_submit' in request.POST:
            context['applicant_form'] = form
        
        return self.render_to_response(context)


class PasswordResetRequestView(FormView):
    """Request password reset via email."""

    template_name = "accounts/password_reset_request.html"
    form_class = PasswordResetRequestForm
    success_url = reverse_lazy("password-reset-email-sent")

    def form_valid(self, form):
        email = form.cleaned_data['email']
        try:
            user = User.objects.get(email=email, is_active=True)
            
            # Generate password reset token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Build reset URL
            current_site = get_current_site(self.request)
            reset_url = f"{self.request.scheme}://{current_site.domain}/auth/password/reset/confirm/{uid}/{token}/"
            
            # Send password reset email synchronously
            subject = "POSB Recruitment Portal - Password Reset Request"
            html_message = render_to_string('accounts/emails/password_reset_email.html', {
                'user': user,
                'reset_url': reset_url,
                'site_name': current_site.name,
            })
            
            try:
                send_mail(
                    subject,
                    f"Please click the following link to reset your password: {reset_url}",
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                
                # Log audit event
                log_audit_event(
                    actor=user,
                    action="PASSWORD_RESET_REQUESTED",
                    action_description=f"Password reset requested for {user.email}",
                    request=self.request,
                )
                
                # Show success message
                messages.success(
                    self.request,
                    "Password reset instructions have been sent to your email address."
                )
                return super().form_valid(form)
            except (TimeoutError, ConnectionError, OSError) as e:
                # Network-related errors (timeout, connection refused, etc.)
                log_system_event(
                    level='ERROR',
                    source='SYSTEM',
                    message=f'Network error sending password reset email: {str(e)}',
                    module='accounts.views',
                    function='PasswordResetRequestView.form_valid',
                    related_user=user
                )
                messages.error(
                    self.request,
                    "We're experiencing network issues. Please try again in a few moments, or contact support if the problem persists."
                )
                return self.form_invalid(form)
            except Exception as e:
                # Other email errors
                log_system_event(
                    level='ERROR',
                    source='SYSTEM',
                    message=f'Failed to send password reset email: {str(e)}',
                    module='accounts.views',
                    function='PasswordResetRequestView.form_valid',
                    related_user=user
                )
                messages.error(
                    self.request,
                    "We couldn't send the password reset email. Please check your email address and try again, or contact support."
                )
                return self.form_invalid(form)
            
        except User.DoesNotExist:
            # Notify user that account doesn't exist
            messages.error(
                self.request,
                "No account found with this email address. Please check your email or register for a new account."
            )
            return self.form_invalid(form)


class PasswordResetEmailSentView(TemplateView):
    """Confirmation page after password reset email is sent."""

    template_name = "accounts/password_reset_email_sent.html"


class PasswordResetConfirmView(FormView):
    """Confirm password reset with new password."""

    template_name = "accounts/password_reset_confirm.html"
    form_class = PasswordResetConfirmForm
    success_url = reverse_lazy("login")

    def dispatch(self, request, *args, **kwargs):
        """Validate token and user before showing form."""
        self.uidb64 = kwargs.get('uidb64')
        self.token = kwargs.get('token')
        
        try:
            uid = force_str(urlsafe_base64_decode(self.uidb64))
            self.user = User.objects.get(pk=uid, is_active=True)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            self.user = None
        
        if self.user is None or not default_token_generator.check_token(self.user, self.token):
            messages.error(request, "Invalid or expired password reset link.")
            return redirect("password-reset-request")
        
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Set new password and log the event."""
        new_password = form.cleaned_data['new_password1']
        self.user.set_password(new_password)
        self.user.save()
        
        # Log audit event
        log_audit_event(
            actor=self.user,
            action="PASSWORD_RESET_COMPLETED",
            action_description=f"Password reset completed for {self.user.email}",
            request=self.request,
        )
        
        messages.success(
            self.request,
            "Your password has been reset successfully. Please login with your new password."
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.user
        return context
