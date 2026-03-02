"""
Forms for job management (server-rendered).
"""
from django import forms
from .models import Skill, EducationLevel, Country


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


class EducationLevelForm(forms.ModelForm):
    class Meta:
        model = EducationLevel
        fields = ["name", "d365_code", "sort_order", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4',
                'placeholder': 'e.g. Bachelor\'s Degree'
            }),
            "d365_code": forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4',
                'placeholder': 'D365 education level code (optional)'
            }),
            "sort_order": forms.NumberInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4',
                'placeholder': '0'
            }),
        }


class CountryForm(forms.ModelForm):
    class Meta:
        model = Country
        fields = ["name", "iso2", "iso3", "sort_order", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4',
                'placeholder': 'e.g. Zimbabwe'
            }),
            "iso2": forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4',
                'placeholder': 'e.g. ZW',
                'maxlength': '2',
                'style': 'text-transform: uppercase;'
            }),
            "iso3": forms.TextInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4',
                'placeholder': 'e.g. ZWE',
                'maxlength': '3',
                'style': 'text-transform: uppercase;'
            }),
            "sort_order": forms.NumberInput(attrs={
                'class': 'w-full rounded-lg border-gray-200 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-primary focus:ring-primary h-11 px-4',
                'placeholder': '0 = top of dropdown'
            }),
        }
        help_texts = {
            "iso2": "ISO 3166-1 alpha-2 code. D365 Country field uses this format.",
            "iso3": "ISO 3166-1 alpha-3 code. D365 Citizenship field uses this format.",
            "sort_order": "Lower values appear first in dropdowns. Use 0 for frequently used countries.",
        }

    def clean_iso2(self):
        return self.cleaned_data["iso2"].upper()

    def clean_iso3(self):
        return self.cleaned_data["iso3"].upper()
