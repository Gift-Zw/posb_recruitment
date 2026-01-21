"""
Serializers for jobs app.
"""
from rest_framework import serializers
from .models import JobCategory, Skill, JobAdvert


class SkillSerializer(serializers.ModelSerializer):
    """Serializer for Skill model."""
    
    class Meta:
        model = Skill
        fields = ['id', 'name', 'description']


class JobCategorySerializer(serializers.ModelSerializer):
    """Serializer for JobCategory model."""
    
    class Meta:
        model = JobCategory
        fields = ['id', 'name', 'description']


class JobAdvertListSerializer(serializers.ModelSerializer):
    """Serializer for job advert list (public view)."""
    category = JobCategorySerializer(read_only=True)
    required_skills = SkillSerializer(many=True, read_only=True)
    is_open = serializers.SerializerMethodField()
    
    class Meta:
        model = JobAdvert
        fields = [
            'id', 'title', 'category', 'description', 'responsibilities',
            'required_skills', 'application_deadline', 'status', 'is_open',
            'created_at'
        ]
    
    def get_is_open(self, obj):
        return obj.is_open_for_applications()


class JobAdvertDetailSerializer(serializers.ModelSerializer):
    """Serializer for job advert detail (includes HR-only fields)."""
    category = JobCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=JobCategory.objects.all(),
        source='category',
        write_only=True
    )
    required_skills = SkillSerializer(many=True, read_only=True)
    required_skill_ids = serializers.PrimaryKeyRelatedField(
        queryset=Skill.objects.all(),
        source='required_skills',
        many=True,
        write_only=True,
        required=False
    )
    is_open = serializers.SerializerMethodField()
    
    class Meta:
        model = JobAdvert
        fields = [
            'id', 'title', 'category', 'category_id', 'description', 'responsibilities',
            'required_skills', 'required_skill_ids', 'application_deadline',
            'status', 'shortlist_count', 'ai_shortlisting_instructions',
            'is_open', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_is_open(self, obj):
        return obj.is_open_for_applications()
