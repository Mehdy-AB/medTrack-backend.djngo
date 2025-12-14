"""Serializers for evaluations app."""
from rest_framework import serializers
from django.utils import timezone
from .models import Evaluation, EvaluationSection
from utils.service_client import get_profile_client, get_auth_client, get_core_client


class EvaluationSectionSerializer(serializers.ModelSerializer):
    """Basic serializer for evaluation sections."""
    
    class Meta:
        model = EvaluationSection
        fields = ['id', 'evaluation_id', 'criterion', 'score', 'comments']
        read_only_fields = ['id']


class CreateEvaluationSectionRequest(serializers.Serializer):
    """Request serializer for creating evaluation section."""
    criterion = serializers.CharField(max_length=255)
    score = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True, min_value=0, max_value=10)
    comments = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class EvaluationSerializer(serializers.ModelSerializer):
    """Basic serializer for evaluations."""
    
    class Meta:
        model = Evaluation
        fields = [
            'id', 'student_id', 'offer_id', 'evaluator_id', 'grade',
            'comments', 'submitted_at', 'validated', 'validated_at', 'metadata'
        ]
        read_only_fields = ['id', 'submitted_at']


class CreateEvaluationRequest(serializers.Serializer):
    """Request serializer for creating evaluation."""
    student_id = serializers.UUIDField()
    offer_id = serializers.UUIDField()
    evaluator_id = serializers.UUIDField(required=False)  # Optional for testing
    grade = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True, min_value=0, max_value=20)
    comments = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    sections = CreateEvaluationSectionRequest(many=True, required=False)


class UpdateEvaluationRequest(serializers.Serializer):
    """Request serializer for updating evaluation."""
    grade = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True, min_value=0, max_value=20)
    comments = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    sections = serializers.ListField(required=False)


class ValidateEvaluationRequest(serializers.Serializer):
    """Request serializer for validating evaluation."""
    validated = serializers.BooleanField(required=False, default=True)


class EvaluationWithDetailsSerializer(serializers.ModelSerializer):
    """Evaluation with nested student, offer, evaluator, and sections."""
    student = serializers.SerializerMethodField()
    offer = serializers.SerializerMethodField()
    evaluator = serializers.SerializerMethodField()
    sections = serializers.SerializerMethodField()
    
    class Meta:
        model = Evaluation
        fields = [
            'id', 'student_id', 'offer_id', 'evaluator_id', 'grade',
            'comments', 'submitted_at', 'validated', 'validated_at', 'metadata',
            'student', 'offer', 'evaluator', 'sections'
        ]
        read_only_fields = ['id', 'submitted_at']
    
    def get_student(self, obj):
        """Fetch student details from PROFILE-SERVICE."""
        try:
            profile_client = get_profile_client()
            student = profile_client.get_student_details(obj.student_id)
            if student:
                return {
                    'first_name': student.get('first_name'),
                    'last_name': student.get('last_name'),
                    'student_number': student.get('student_number'),
                }
        except Exception as e:
            print(f"Error fetching student details: {e}")
        return None
    
    def get_offer(self, obj):
        """Fetch offer details from CORE-SERVICE."""
        try:
            core_client = get_core_client()
            offer = core_client.get_offer_details(obj.offer_id)
            if offer:
                return {
                    'title': offer.get('title'),
                    'service_name': offer.get('service', {}).get('name') if offer.get('service') else None,
                    'establishment_name': offer.get('establishment', {}).get('name') if offer.get('establishment') else None,
                }
        except Exception as e:
            print(f"Error fetching offer details: {e}")
        return {
            'title': None,
            'service_name': None,
            'establishment_name': None,
        }
    
    def get_evaluator(self, obj):
        """Fetch evaluator details from AUTH-SERVICE."""
        try:
            auth_client = get_auth_client()
            evaluator = auth_client.get_user_details(obj.evaluator_id)
            if evaluator:
                return {
                    'first_name': evaluator.get('first_name'),
                    'last_name': evaluator.get('last_name'),
                }
        except Exception as e:
            print(f"Error fetching evaluator details: {e}")
        return None
    
    def get_sections(self, obj):
        """Get evaluation sections."""
        sections = EvaluationSection.objects.filter(evaluation=obj).order_by('id')
        return EvaluationSectionSerializer(sections, many=True).data


class PaginatedEvaluations(serializers.Serializer):
    """Paginated response for evaluations."""
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = EvaluationWithDetailsSerializer(many=True)
