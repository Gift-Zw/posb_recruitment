"""
Serializers for jobs app.
"""
from rest_framework import serializers
from .models import Skill, Certification, JobAdvert


class SkillSerializer(serializers.ModelSerializer):
    """Serializer for Skill model."""
    
    class Meta:
        model = Skill
        fields = ['id', 'name', 'description']


class CertificationSerializer(serializers.ModelSerializer):
    """Serializer for Certification model."""
    
    class Meta:
        model = Certification
        fields = ['id', 'name', 'description']


class JobAdvertListSerializer(serializers.ModelSerializer):
    """Serializer for job advert list (public view)."""
    is_open = serializers.SerializerMethodField()
    
    class Meta:
        model = JobAdvert
        fields = [
            'id', 'recruiting_id', 'job_id', 'job_title', 'job_function',
            'job_description', 'location', 'job_type', 'end_date',
            'status', 'is_open', 'created_at'
        ]
    
    def get_is_open(self, obj):
        return obj.is_open_for_applications()


class JobAdvertDetailSerializer(serializers.ModelSerializer):
    """Serializer for job advert detail (includes all fields)."""
    is_open = serializers.SerializerMethodField()
    
    class Meta:
        model = JobAdvert
        fields = [
            'id', 'recruiting_id', 'job_id', 'job_title', 'job_description',
            'skills', 'certificates', 'education', 'job_tasks', 'responsibilities',
            'years_of_experience', 'location', 'job_type', 'job_function',
            'end_date', 'status', 'is_open', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_is_open(self, obj):
        return obj.is_open_for_applications()
