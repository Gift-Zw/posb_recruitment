"""
Forms for job management (server-rendered).
"""
from django import forms
from .models import Skill, Certification


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


class CertificationForm(forms.ModelForm):
    class Meta:
        model = Certification
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4',
                'placeholder': 'Certification name'
            }),
            "description": forms.Textarea(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary p-3',
                'rows': 4,
                'placeholder': 'Certification description (optional)'
            }),
        }
