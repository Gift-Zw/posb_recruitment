"""
Admin configuration for jobs app.
"""
from django.contrib import admin
from .models import Skill, Certification, JobAdvert


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(JobAdvert)
class JobAdvertAdmin(admin.ModelAdmin):
    list_display = ['job_title', 'job_id', 'recruiting_id', 'job_function', 'status', 'end_date', 'created_at']
    list_filter = ['status', 'job_function', 'created_at', 'end_date']
    search_fields = ['job_title', 'job_id', 'recruiting_id', 'job_description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('D365 Information', {
            'fields': ('recruiting_id', 'job_id', 'job_title', 'job_function', 'status')
        }),
        ('Job Details', {
            'fields': ('job_description', 'responsibilities', 'job_tasks', 'skills', 'education', 'certificates')
        }),
        ('Requirements', {
            'fields': ('years_of_experience', 'location', 'job_type')
        }),
        ('Application Settings', {
            'fields': ('end_date',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )
