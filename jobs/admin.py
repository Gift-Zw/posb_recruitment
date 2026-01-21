"""
Admin configuration for jobs app.
"""
from django.contrib import admin
from .models import JobCategory, Skill, JobAdvert


@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name', 'description']


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(JobAdvert)
class JobAdvertAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'status', 'application_deadline', 'shortlist_count', 'created_at']
    list_filter = ['status', 'category', 'created_at', 'application_deadline']
    search_fields = ['title', 'description']
    filter_horizontal = ['required_skills']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'category', 'status')
        }),
        ('Job Details', {
            'fields': ('description', 'responsibilities', 'required_skills')
        }),
        ('Application Settings', {
            'fields': ('application_deadline', 'shortlist_count')
        }),
        ('AI Shortlisting', {
            'fields': ('ai_shortlisting_instructions',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )
