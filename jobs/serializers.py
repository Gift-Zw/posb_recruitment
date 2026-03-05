"""
Serializers for jobs app.
"""
from rest_framework import serializers
from .models import Skill, EducationLevel, Country, JobAdvert


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name', 'description']


class EducationLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = EducationLevel
        fields = ['id', 'name', 'd365_code', 'sort_order']


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['id', 'name', 'iso2', 'iso3', 'is_active', 'sort_order']


class JobAdvertListSerializer(serializers.ModelSerializer):
    is_open = serializers.SerializerMethodField()
    
    class Meta:
        model = JobAdvert
        fields = [
            'id', 'recruiting_id', 'job_id', 'job_title',
            'job_description', 'location', 'job_type', 'end_date',
            'status', 'is_open', 'created_at'
        ]
    
    def get_is_open(self, obj):
        return obj.is_open_for_applications()


class JobAdvertDetailSerializer(serializers.ModelSerializer):
    is_open = serializers.SerializerMethodField()
    
    class Meta:
        model = JobAdvert
        fields = [
            'id', 'recruiting_id', 'job_id', 'job_title', 'job_description',
            'skills', 'certificates', 'education', 'job_tasks', 'responsibilities',
            'years_of_experience', 'location', 'job_type',
            'end_date', 'status', 'is_open', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_is_open(self, obj):
        return obj.is_open_for_applications()
