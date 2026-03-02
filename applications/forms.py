"""
Forms for application submission (server-rendered).
"""
from django import forms
from applications.models import ApplicantProfile, ApplicantProfileDocument
from jobs.models import EducationLevel, Country

FIELD_CLASS = 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-10 px-3 text-sm'


class ApplicantProfileForm(forms.ModelForm):
    """Collect applicant profile data aligned with D365 Applicant Import fields."""

    skills_text = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': FIELD_CLASS,
            'placeholder': 'e.g., Python; JavaScript; Project Management'
        }),
        help_text="Enter your skills separated by semicolons (;)",
    )

    class Meta:
        model = ApplicantProfile
        fields = [
            "phone_number", "alternate_phone", "email",
            "middle_name", "date_of_birth", "gender", "citizenship",
            "id_number", "marital_status",
            "address_line_1", "address_line_2", "city",
            "state_province", "postal_code", "country",
            "current_job_title", "education_level",
            "professional_summary", "cover_letter",
            "linkedin_url", "portfolio_url",
            "availability_date", "current_salary", "expected_salary", "notice_period",
        ]
        widgets = {
            "phone_number": forms.TextInput(attrs={'class': FIELD_CLASS, 'placeholder': '+263 77 123 4567'}),
            "alternate_phone": forms.TextInput(attrs={'class': FIELD_CLASS, 'placeholder': 'Optional'}),
            "email": forms.EmailInput(attrs={'class': FIELD_CLASS, 'placeholder': 'your.email@example.com'}),
            "middle_name": forms.TextInput(attrs={'class': FIELD_CLASS, 'placeholder': 'Middle name (optional)'}),
            "date_of_birth": forms.DateInput(attrs={'type': 'date', 'class': FIELD_CLASS}),
            "gender": forms.Select(attrs={'class': FIELD_CLASS}),
            "citizenship": forms.Select(attrs={'class': FIELD_CLASS}),
            "id_number": forms.TextInput(attrs={'class': FIELD_CLASS, 'placeholder': 'National ID number'}),
            "marital_status": forms.Select(attrs={'class': FIELD_CLASS}),
            "address_line_1": forms.TextInput(attrs={'class': FIELD_CLASS, 'placeholder': 'Street address'}),
            "address_line_2": forms.TextInput(attrs={'class': FIELD_CLASS, 'placeholder': 'Apartment, suite, etc. (optional)'}),
            "city": forms.TextInput(attrs={'class': FIELD_CLASS, 'placeholder': 'City'}),
            "state_province": forms.TextInput(attrs={'class': FIELD_CLASS, 'placeholder': 'State/Province'}),
            "postal_code": forms.TextInput(attrs={'class': FIELD_CLASS, 'placeholder': 'Postal / Zip Code'}),
            "country": forms.Select(attrs={'class': FIELD_CLASS}),
            "current_job_title": forms.TextInput(attrs={'class': FIELD_CLASS, 'placeholder': 'e.g., Software Developer'}),
            "education_level": forms.Select(attrs={'class': FIELD_CLASS}),
            "professional_summary": forms.Textarea(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary p-3 text-sm',
                'rows': 5, 'placeholder': 'Tell us about yourself...'
            }),
            "cover_letter": forms.Textarea(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary p-3 text-sm',
                'rows': 6, 'placeholder': 'Write a cover letter explaining why you are interested in this position...'
            }),
            "linkedin_url": forms.URLInput(attrs={'class': FIELD_CLASS, 'placeholder': 'https://linkedin.com/in/yourprofile'}),
            "portfolio_url": forms.URLInput(attrs={'class': FIELD_CLASS, 'placeholder': 'https://yourportfolio.com'}),
            "availability_date": forms.DateInput(attrs={'type': 'date', 'class': FIELD_CLASS}),
            "current_salary": forms.NumberInput(attrs={'class': FIELD_CLASS, 'placeholder': 'Current salary (optional)'}),
            "expected_salary": forms.NumberInput(attrs={'class': FIELD_CLASS, 'placeholder': 'Expected salary (optional)'}),
            "notice_period": forms.TextInput(attrs={'class': FIELD_CLASS, 'placeholder': 'e.g., 2 weeks, 1 month'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['education_level'].queryset = EducationLevel.objects.filter(is_active=True)
        self.fields['citizenship'].queryset = Country.objects.filter(is_active=True)
        self.fields['citizenship'].empty_label = '— Select citizenship —'
        self.fields['country'].queryset = Country.objects.filter(is_active=True)
        self.fields['country'].empty_label = '— Select country —'


class DocumentUploadForm(forms.ModelForm):
    """Form for uploading documents to applicant profile."""
    
    class Meta:
        model = ApplicantProfileDocument
        fields = ['document_type', 'file', 'description']
        widgets = {
            'document_type': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4'
            }),
            'file': forms.FileInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4',
                'accept': '.pdf,.doc,.docx'
            }),
            'description': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4',
                'placeholder': 'Optional description'
            }),
        }
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            allowed_exts = ['.pdf', '.doc', '.docx']
            if not any(file.name.lower().endswith(ext) for ext in allowed_exts):
                raise forms.ValidationError("Allowed file types: PDF, DOC, DOCX.")
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError("File too large (max 10MB).")
        return file
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get('file'):
            instance.file_name = self.cleaned_data['file'].name
            instance.file_size = self.cleaned_data['file'].size
        if commit:
            instance.save()
        return instance


class ApplicationForm(forms.Form):
    """Application submission — CV upload and cover letter."""

    cover_letter = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary p-3 text-sm',
            'rows': 6,
            'placeholder': 'Write a cover letter explaining why you are interested in this position...'
        })
    )
    cv_file = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary py-2.5 px-4 text-sm file:mr-6 file:py-2.5 file:px-5 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary file:text-white hover:file:bg-primary/90',
            'accept': '.pdf,.doc,.docx'
        })
    )

    def clean_cv_file(self):
        file = self.cleaned_data["cv_file"]
        allowed_exts = [".pdf", ".doc", ".docx"]
        if not any(file.name.lower().endswith(ext) for ext in allowed_exts):
            raise forms.ValidationError("Allowed file types: pdf, doc, docx.")
        if file.size > 10 * 1024 * 1024:
            raise forms.ValidationError("File too large (max 10MB).")
        return file
