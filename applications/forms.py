"""
Forms for application submission (server-rendered).
"""
import json
from django import forms
from django.core.exceptions import ValidationError
from applications.models import ApplicantProfile, ApplicantProfileDocument
from jobs.models import Skill


class ApplicantProfileForm(forms.ModelForm):
    """Collect detailed applicant profile data."""

    education = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": 'e.g. [{"institution": "...", "degree": "...", "field": "...", "start_year": "...", "end_year": "..."}]'}),
        help_text="JSON list of education entries.",
    )
    experience = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": 'e.g. [{"company": "...", "position": "...", "start_date": "...", "end_date": "...", "current": false}]'}),
        help_text="JSON list of experience entries.",
    )
    languages = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2, "placeholder": 'e.g. [{"language": "English", "proficiency": "Fluent"}]'}),
        help_text="JSON list of languages.",
    )
    certifications = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2, "placeholder": 'e.g. [{"name": "...", "issuing_organization": "...", "issue_date": "..."}]'}),
        help_text="JSON list of certifications.",
    )
    references = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2, "placeholder": 'e.g. [{"name": "...", "position": "...", "company": "...", "email": "...", "phone": "..."}]'}),
        help_text="JSON list of references.",
    )

    class Meta:
        model = ApplicantProfile
        fields = [
            # Contact Information
            "phone_number",
            "alternate_phone",
            "email",
            # Personal Information
            "date_of_birth",
            "gender",
            "nationality",
            "id_number",
            "marital_status",
            # Address Information
            "address_line_1",
            "address_line_2",
            "city",
            "state_province",
            "postal_code",
            "country",
            # Professional Summary
            "professional_summary",
            # Skills (ManyToMany - handled separately in view)
            "skills",
            # Note: education, experience, languages, certifications, references, and projects
            # are JSON fields handled separately via JavaScript and submitted via hidden inputs
            # Emergency Contact
            "emergency_contact_name",
            "emergency_contact_relationship",
            "emergency_contact_phone",
            "emergency_contact_email",
            # Additional Information
            "cover_letter",
            "linkedin_url",
            "github_url",
            "twitter_url",
            "facebook_url",
            "instagram_url",
            "youtube_url",
            "behance_url",
            "dribbble_url",
            "medium_url",
            "stackoverflow_url",
            "portfolio_url",
            "availability_date",
            "current_salary",
            "expected_salary",
            "notice_period",
        ]
        widgets = {
            "phone_number": forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-10 px-3 text-sm',
                'placeholder': 'e.g., +263 77 123 4567'
            }),
            "alternate_phone": forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-10 px-3 text-sm',
                'placeholder': 'Optional'
            }),
            "email": forms.EmailInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-10 px-3 text-sm',
                'placeholder': 'your.email@example.com'
            }),
            "date_of_birth": forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-10 px-3 text-sm'
            }),
            "gender": forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-10 px-3 text-sm'
            }),
            "nationality": forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-10 px-3 text-sm',
                'placeholder': 'e.g., Zimbabwean'
            }),
            "id_number": forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-10 px-3 text-sm',
                'placeholder': 'National ID number'
            }),
            "marital_status": forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-10 px-3 text-sm'
            }),
            "address_line_1": forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-10 px-3 text-sm',
                'placeholder': 'Street address'
            }),
            "address_line_2": forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-10 px-3 text-sm',
                'placeholder': 'Apartment, suite, etc. (optional)'
            }),
            "city": forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-10 px-3 text-sm',
                'placeholder': 'City'
            }),
            "state_province": forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-10 px-3 text-sm',
                'placeholder': 'State/Province'
            }),
            "postal_code": forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-10 px-3 text-sm',
                'placeholder': 'Postal code'
            }),
            "country": forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-10 px-3 text-sm',
                'placeholder': 'Country'
            }),
            "professional_summary": forms.Textarea(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary p-3 text-sm',
                'rows': 5,
                'placeholder': 'Tell us about yourself, your professional background, achievements, and career goals...'
            }),
            "skills": forms.CheckboxSelectMultiple(attrs={
                'class': 'space-y-2'
            }),
            "emergency_contact_name": forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-10 px-3 text-sm',
                'placeholder': 'Full name'
            }),
            "emergency_contact_relationship": forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-10 px-3 text-sm',
                'placeholder': 'e.g., Spouse, Parent, Sibling'
            }),
            "emergency_contact_phone": forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-10 px-3 text-sm',
                'placeholder': 'Phone number'
            }),
            "emergency_contact_email": forms.EmailInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-10 px-3 text-sm',
                'placeholder': 'Email address'
            }),
            "cover_letter": forms.Textarea(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary p-3 text-sm',
                'rows': 6,
                'placeholder': 'Write a cover letter explaining why you are interested in this position...'
            }),
            "linkedin_url": forms.URLInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-10 px-3 text-sm',
                'placeholder': 'https://linkedin.com/in/yourprofile'
            }),
            "github_url": forms.URLInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-10 px-3 text-sm',
                'placeholder': 'https://github.com/yourusername'
            }),
            "portfolio_url": forms.URLInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-10 px-3 text-sm',
                'placeholder': 'https://yourportfolio.com'
            }),
            "availability_date": forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-10 px-3 text-sm'
            }),
            "current_salary": forms.NumberInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-10 px-3 text-sm',
                'placeholder': 'Current salary (optional)'
            }),
            "expected_salary": forms.NumberInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-10 px-3 text-sm',
                'placeholder': 'Expected salary (optional)'
            }),
            "notice_period": forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-10 px-3 text-sm',
                'placeholder': 'e.g., 2 weeks, 1 month'
            }),
        }

    def clean_education(self):
        return self._parse_json_field("education")

    def clean_experience(self):
        return self._parse_json_field("experience")
    
    def clean_languages(self):
        return self._parse_json_field("languages")
    
    def clean_certifications(self):
        return self._parse_json_field("certifications")
    
    def clean_references(self):
        return self._parse_json_field("references")

    def _parse_json_field(self, field):
        value = self.cleaned_data.get(field, "")
        if not value:
            return []
        try:
            parsed = json.loads(value)
            if not isinstance(parsed, list):
                raise ValidationError(f"{field} must be a JSON array.")
            return parsed
        except json.JSONDecodeError:
            raise ValidationError("Invalid JSON format.")


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
                raise ValidationError("Allowed file types: PDF, DOC, DOCX.")
            if file.size > 10 * 1024 * 1024:  # 10MB
                raise ValidationError("File too large (max 10MB).")
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
    """Application submission data."""

    cover_letter = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary p-3 text-sm',
            'rows': 6,
            'placeholder': 'Write a cover letter explaining why you are interested in this position...'
        })
    )
    reuse_last = forms.BooleanField(
        required=False,
        initial=True,
        help_text="Reuse previous application data if available.",
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary'
        })
    )
    cv_file = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-10 px-3 text-sm file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary file:text-white hover:file:bg-primary/90',
            'accept': '.pdf,.doc,.docx'
        })
    )

    def clean_cv_file(self):
        file = self.cleaned_data["cv_file"]
        allowed_exts = [".pdf", ".doc", ".docx"]
        if not any(file.name.lower().endswith(ext) for ext in allowed_exts):
            raise ValidationError("Allowed file types: pdf, doc, docx.")
        if file.size > 10 * 1024 * 1024:
            raise ValidationError("File too large (max 10MB).")
        return file
