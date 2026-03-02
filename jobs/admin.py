"""
Admin configuration for jobs app.
"""
from django.contrib import admin
from .models import Skill, EducationLevel, Country, JobAdvert


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(EducationLevel)
class EducationLevelAdmin(admin.ModelAdmin):
    list_display = ['name', 'd365_code', 'sort_order', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'd365_code']


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['name', 'iso2', 'iso3', 'is_active', 'sort_order']
    list_filter = ['is_active']
    search_fields = ['name', 'iso2', 'iso3']
    list_editable = ['sort_order', 'is_active']


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
