"""
Admin configuration for applications app.
"""
from django.contrib import admin
from .models import ApplicantProfile, Application, ApplicationDocument, ApplicantProfileDocument, ApplicationData


@admin.register(ApplicantProfile)
class ApplicantProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number', 'nationality', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    filter_horizontal = ['skills']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'job_advert', 'status', 'ai_score', 'ai_ranking', 'submitted_at']
    list_filter = ['status', 'submitted_at', 'job_advert__job_function']
    search_fields = ['applicant__email', 'job_advert__job_title']
    readonly_fields = ['submitted_at', 'updated_at', 'ai_shortlisted_at']
    fieldsets = (
        ('Application Details', {
            'fields': ('applicant', 'job_advert', 'status')
        }),
        ('AI Shortlisting', {
            'fields': ('ai_score', 'ai_ranking', 'ai_explanation', 'ai_shortlisted_at')
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'updated_at')
        }),
    )


@admin.register(ApplicationData)
class ApplicationDataAdmin(admin.ModelAdmin):
    list_display = ['application', 'phone_number', 'email', 'nationality', 'created_at']
    list_filter = ['created_at', 'nationality']
    search_fields = ['application__applicant__email', 'phone_number', 'email']
    readonly_fields = ['created_at']
    fieldsets = (
        ('Application', {
            'fields': ('application',)
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'email', 'address')
        }),
        ('Personal Information', {
            'fields': ('date_of_birth', 'nationality')
        }),
        ('Professional Information', {
            'fields': ('skills', 'education', 'experience', 'cover_letter')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )


@admin.register(ApplicationDocument)
class ApplicationDocumentAdmin(admin.ModelAdmin):
    list_display = ['application', 'document_type', 'file_name', 'file_size', 'uploaded_at']
    list_filter = ['document_type', 'uploaded_at']
    search_fields = ['application__applicant__email', 'file_name']
    readonly_fields = ['uploaded_at']


@admin.register(ApplicantProfileDocument)
class ApplicantProfileDocumentAdmin(admin.ModelAdmin):
    list_display = ['applicant_profile', 'document_type', 'file_name', 'file_size', 'uploaded_at']
    list_filter = ['document_type', 'uploaded_at']
    search_fields = ['applicant_profile__user__email', 'file_name', 'description']
    readonly_fields = ['uploaded_at', 'file_size']
