"""
Forms for accounts app (server-rendered flows).
"""
from django import forms
from django.contrib.auth import authenticate
from .models import User
from applications.models import ApplicantProfile
from jobs.models import Skill


class RegistrationForm(forms.ModelForm):
    """Form for applicant registration with password confirmation."""

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        min_length=8,
        help_text="Minimum 8 characters.",
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput,
        min_length=8,
    )

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name"]

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password1") != cleaned.get("password2"):
            raise forms.ValidationError("Passwords do not match.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        # Set is_active=True so they can login, but is_verified=False so they must verify OTP
        user.is_active = True
        user.is_verified = False
        user.user_type = 'APPLICANT'  # Only applicants can self-register
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    """Email/password login form."""

    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get("email")
        password = cleaned.get("password")
        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise forms.ValidationError("Invalid email or password.")
            
            # Block disabled accounts (unless they are unverified applicants)
            # Unverified applicants are active but not verified, and will be redirected to OTP
            if not user.is_active:
                raise forms.ValidationError("Account is disabled.")
            
            # Store user even if not verified - we'll handle redirect in the view
            # Superusers, staff, and employees can bypass OTP verification
            # Only applicants must verify email via OTP
            cleaned["user"] = user
            cleaned["needs_verification"] = not user.is_verified and user.is_applicant()
        return cleaned


class ManagementLoginForm(forms.Form):
    """Management portal login form - only for employees."""

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full h-14 px-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary focus:border-primary transition-all',
            'placeholder': 'your.email@posb.co.zw'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full h-14 px-4 pr-12 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary focus:border-primary transition-all',
            'placeholder': 'Enter your password'
        })
    )

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get("email")
        password = cleaned.get("password")
        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise forms.ValidationError("Invalid email or password.")
            
            if not user.is_active:
                raise forms.ValidationError("Account is disabled.")
            
            # Only employees and superusers can access management portal
            if not user.is_employee() and not user.is_superuser:
                raise forms.ValidationError("This login is for HR staff only. Please use the public portal login.")
            
            cleaned["user"] = user
        return cleaned


class OTPRequestForm(forms.Form):
    """Form for requesting OTP."""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full h-14 px-4 rounded-lg border border-stone-200 dark:border-stone-700 bg-white dark:bg-stone-900 text-stone-900 dark:text-white focus:ring-2 focus:ring-primary focus:border-primary transition-all',
            'placeholder': 'your.email@example.com'
        })
    )
    purpose = forms.CharField(
        required=False,
        initial='email_verification',
        widget=forms.HiddenInput()
    )


class OTPVerifyForm(forms.Form):
    """Form for verifying OTP."""
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'w-full h-14 px-4 rounded-lg border border-stone-200 dark:border-stone-700 bg-white dark:bg-stone-900 text-stone-900 dark:text-white focus:ring-2 focus:ring-primary focus:border-primary transition-all',
            'placeholder': 'your.email@example.com'
        })
    )
    code = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'w-full h-14 px-4 rounded-lg border border-stone-200 dark:border-stone-700 bg-white dark:bg-stone-900 text-stone-900 dark:text-white focus:ring-2 focus:ring-primary focus:border-primary transition-all',
            'placeholder': 'Enter 6-digit code'
        })
    )
    purpose = forms.CharField(
        required=False,
        initial='email_verification',
        widget=forms.HiddenInput()
    )


class ProfileForm(forms.ModelForm):
    """Update basic user information."""

    class Meta:
        model = User
        fields = ["first_name", "last_name"]


class ApplicantProfileForm(forms.ModelForm):
    """Form for updating ApplicantProfile details on the profile page."""
    class Meta:
        model = ApplicantProfile
        exclude = ['user']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'professional_summary': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Write a brief professional summary about yourself, your skills, and career goals...'}),
            'cover_letter': forms.Textarea(attrs={'rows': 4}),
            'gender': forms.Select(attrs={'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4'}),
            'marital_status': forms.Select(attrs={'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4'}),
            'education_level': forms.Select(attrs={'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4'}),
            'citizenship': forms.Select(attrs={'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4'}),
            'country': forms.Select(attrs={'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from jobs.models import Country, EducationLevel
        self.fields['citizenship'].queryset = Country.objects.filter(is_active=True)
        self.fields['citizenship'].empty_label = '— Select citizenship —'
        self.fields['country'].queryset = Country.objects.filter(is_active=True)
        self.fields['country'].empty_label = '— Select country —'
        self.fields['education_level'].queryset = EducationLevel.objects.filter(is_active=True)


class PasswordChangeForm(forms.Form):
    """Form for changing user password."""
    current_password = forms.CharField(widget=forms.PasswordInput, label="Current Password")
    new_password1 = forms.CharField(widget=forms.PasswordInput, label="New Password", min_length=8)
    new_password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm New Password", min_length=8)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise forms.ValidationError("Your current password was entered incorrectly. Please enter it again.")
        return current_password

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')

        if new_password1 and new_password2 and new_password1 != new_password2:
            self.add_error('new_password2', "New passwords do not match.")
        return cleaned_data


class PasswordResetRequestForm(forms.Form):
    """Form for requesting password reset."""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full h-14 px-4 rounded-lg border border-stone-200 dark:border-stone-700 bg-white dark:bg-stone-900 text-stone-900 dark:text-white focus:ring-2 focus:ring-primary focus:border-primary transition-all',
            'placeholder': 'your.email@example.com'
        })
    )


class PasswordResetConfirmForm(forms.Form):
    """Form for confirming password reset with new password."""
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full h-14 px-4 rounded-lg border border-stone-200 dark:border-stone-700 bg-white dark:bg-stone-900 text-stone-900 dark:text-white focus:ring-2 focus:ring-primary focus:border-primary transition-all',
            'placeholder': 'Enter new password'
        }),
        min_length=8,
        help_text="Minimum 8 characters."
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full h-14 px-4 rounded-lg border border-stone-200 dark:border-stone-700 bg-white dark:bg-stone-900 text-stone-900 dark:text-white focus:ring-2 focus:ring-primary focus:border-primary transition-all',
            'placeholder': 'Confirm new password'
        }),
        min_length=8,
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("new_password1") != cleaned.get("new_password2"):
            raise forms.ValidationError("Passwords do not match.")
        return cleaned


class FirstLoginPasswordResetForm(forms.Form):
    """Form for mandatory password change at first login."""
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full h-14 px-4 rounded-lg border border-stone-200 dark:border-stone-700 bg-white dark:bg-stone-900 text-stone-900 dark:text-white focus:ring-2 focus:ring-primary focus:border-primary transition-all',
            'placeholder': 'Enter new password'
        }),
        min_length=8,
        help_text="Minimum 8 characters."
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full h-14 px-4 rounded-lg border border-stone-200 dark:border-stone-700 bg-white dark:bg-stone-900 text-stone-900 dark:text-white focus:ring-2 focus:ring-primary focus:border-primary transition-all',
            'placeholder': 'Confirm new password'
        }),
        min_length=8,
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("new_password1") != cleaned.get("new_password2"):
            raise forms.ValidationError("Passwords do not match.")
        return cleaned


class UserCreateForm(forms.ModelForm):
    """Form for creating new employee/staff user."""
    
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4',
        }),
        min_length=8,
        help_text="Minimum 8 characters. This temporary password will be emailed to the employee."
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4',
        }),
        min_length=8,
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        label="Active",
        help_text="Uncheck to create inactive account"
    )
    
    # Employee Profile fields
    ec_number = forms.CharField(
        required=False,
        label="EC Number",
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4',
        }),
    )
    phone_number = forms.CharField(
        required=False,
        label="Phone Number",
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4',
        }),
    )
    department = forms.CharField(
        required=False,
        label="Department",
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4',
        }),
    )
    job_title = forms.CharField(
        required=False,
        label="Job Title",
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4',
        }),
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'is_active']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4',
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4',
            }),
        }

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        password2 = cleaned.get('password2')
        if password and password2 and password != password2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned


class UserUpdateForm(forms.ModelForm):
    """Form for updating user account."""
    
    password = forms.CharField(
        required=False,
        label="New Password (leave blank to keep current password)",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4',
        }),
        min_length=8,
        help_text="Minimum 8 characters. Leave blank to keep current password."
    )
    password_confirm = forms.CharField(
        required=False,
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4',
        }),
        min_length=8,
    )
    
    # Employee Profile fields
    ec_number = forms.CharField(
        required=False,
        label="EC Number",
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4',
        }),
    )
    phone_number = forms.CharField(
        required=False,
        label="Phone Number",
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4',
        }),
    )
    department = forms.CharField(
        required=False,
        label="Department",
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4',
        }),
    )
    job_title = forms.CharField(
        required=False,
        label="Job Title",
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4',
        }),
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'is_active', 'is_verified']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4',
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-primary focus:ring-primary',
            }),
            'is_verified': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-primary focus:ring-primary',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-fill employee profile fields if they exist
        if self.instance and self.instance.pk:
            if hasattr(self.instance, 'employee_profile'):
                profile = self.instance.employee_profile
                self.fields['ec_number'].initial = profile.ec_number
                self.fields['phone_number'].initial = profile.phone_number
                self.fields['department'].initial = profile.department
                self.fields['job_title'].initial = profile.job_title

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "New passwords do not match.")
        
        if password and not password_confirm:
            self.add_error('password_confirm', "Please confirm the new password.")
        
        if password_confirm and not password:
            self.add_error('password', "Please enter a new password.")
        
        return cleaned_data
