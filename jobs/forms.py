"""
Forms for job management (server-rendered).
"""
from django import forms
from .models import JobCategory, Skill, JobAdvert


class ContactForm(forms.Form):
    """Contact form for FAQ queries."""
    name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full h-14 px-4 rounded-lg border border-stone-200 dark:border-stone-700 bg-white dark:bg-stone-900 text-stone-900 dark:text-white focus:ring-2 focus:ring-primary focus:border-primary transition-all',
            'placeholder': 'Your full name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full h-14 px-4 rounded-lg border border-stone-200 dark:border-stone-700 bg-white dark:bg-stone-900 text-stone-900 dark:text-white focus:ring-2 focus:ring-primary focus:border-primary transition-all',
            'placeholder': 'your.email@example.com'
        })
    )
    subject = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full h-14 px-4 rounded-lg border border-stone-200 dark:border-stone-700 bg-white dark:bg-stone-900 text-stone-900 dark:text-white focus:ring-2 focus:ring-primary focus:border-primary transition-all',
            'placeholder': 'Subject of your query'
        })
    )
    message = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-stone-200 dark:border-stone-700 bg-white dark:bg-stone-900 text-stone-900 dark:text-white focus:ring-2 focus:ring-primary focus:border-primary transition-all',
            'rows': 5,
            'placeholder': 'Please describe your question or concern...'
        })
    )


class JobCategoryForm(forms.ModelForm):
    class Meta:
        model = JobCategory
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4',
                'placeholder': 'Category name'
            }),
            "description": forms.Textarea(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary p-3',
                'rows': 4,
                'placeholder': 'Category description (optional)'
            }),
        }


class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4',
                'placeholder': 'Skill name'
            }),
            "description": forms.Textarea(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary p-3',
                'rows': 4,
                'placeholder': 'Skill description (optional)'
            }),
        }


class JobAdvertForm(forms.ModelForm):
    application_deadline = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            "type": "datetime-local",
            'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4'
        })
    )

    class Meta:
        model = JobAdvert
        fields = [
            "title",
            "category",
            "description",
            "responsibilities",
            "location_type",
            "location",
            "contract_type",
            "education_level",
            "experience_required",
            "required_skills",
            "application_deadline",
            "status",
            "shortlist_count",
            "ai_shortlisting_instructions",
        ]
        widgets = {
            "title": forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4',
                'placeholder': 'Job title'
            }),
            "category": forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4'
            }),
            "description": forms.Textarea(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary p-3',
                'rows': 6,
                'placeholder': 'Full job description'
            }),
            "responsibilities": forms.Textarea(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary p-3',
                'rows': 6,
                'placeholder': 'Key responsibilities and duties'
            }),
            "location_type": forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4'
            }),
            "location": forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4',
                'placeholder': 'e.g., Harare Branch, Bulawayo, Remote'
            }),
            "contract_type": forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4'
            }),
            "education_level": forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4'
            }),
            "experience_required": forms.Textarea(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary p-3',
                'rows': 3,
                'placeholder': 'e.g., "2 years in banking", "5 years customer service experience"'
            }),
            "required_skills": forms.CheckboxSelectMultiple(attrs={
                'class': 'space-y-2'
            }),
            "status": forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4'
            }),
            "shortlist_count": forms.NumberInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4',
                'min': 1
            }),
            "ai_shortlisting_instructions": forms.Textarea(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary p-3',
                'rows': 4,
                'placeholder': 'Custom instructions for AI shortlisting algorithm (optional)'
            }),
        }
