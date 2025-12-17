"""Serializers for applications app."""
from rest_framework import serializers
from django.utils import timezone
from .models import Application
from utils.service_client import get_auth_client, get_profile_client


class CreateApplicationRequest(serializers.Serializer):
    """Serializer for creating a new application."""
    
    offer_id = serializers.UUIDField(required=True)
    student_id = serializers.UUIDField(required=True)
    motivation = serializers.CharField(required=False, allow_blank=True)
    document_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True
    )
    
    def validate_offer_id(self, value):
        """Validate that offer exists."""
        from offers.models import Offer
        if not Offer.objects.filter(id=value).exists():
            raise serializers.ValidationError('Offer does not exist.')
        return value


class UpdateApplicationRequest(serializers.Serializer):
    """Serializer for updating an application (student only)."""
    
    motivation = serializers.CharField(required=False, allow_blank=True)
    document_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True
    )


class UpdateApplicationStatusRequest(serializers.Serializer):
    """Serializer for updating application status (admin/encadrant)."""
    
    status = serializers.ChoiceField(
        choices=['accepted', 'rejected', 'cancelled'],
        required=True
    )
    notes = serializers.CharField(required=False, allow_blank=True)


class ApplicationSerializer(serializers.ModelSerializer):
    """Serializer for Application model."""
    
    offer_id = serializers.UUIDField(source='offer.id', read_only=True)
    
    class Meta:
        model = Application
        fields = [
            'id', 'offer_id', 'student_id', 'submitted_at',
            'status', 'decision_at', 'decision_by', 'notes', 'metadata'
        ]
        read_only_fields = ['id', 'submitted_at', 'decision_at', 'decision_by']
    
    def validate(self, data):
        """Validate application submission."""
        # Only validate on creation
        if not self.instance:
            offer = data.get('offer')
            student_id = data.get('student_id')
            
            # Check for duplicate active application
            active_statuses = [Application.STATUS_SUBMITTED, Application.STATUS_ACCEPTED]
            existing = Application.objects.filter(
                offer=offer,
                student_id=student_id,
                status__in=active_statuses
            ).exists()
            
            if existing:
                raise serializers.ValidationError(
                    'You already have an active application for this offer.'
                )
            
            # Check if offer has available slots
            if not offer.has_available_slots():
                raise serializers.ValidationError(
                    'This offer has no available slots.'
                )
        
        return data


class ApplicationWithDetails(serializers.ModelSerializer):
    """Detailed serializer for single application retrieval with nested data."""
    
    offer_id = serializers.UUIDField(source='offer.id', read_only=True)
    offer = serializers.SerializerMethodField()
    student = serializers.SerializerMethodField()
    decision_by_encadrant = serializers.SerializerMethodField()
    
    class Meta:
        model = Application
        fields = [
            'id', 'offer_id', 'student_id', 'submitted_at',
            'status', 'decision_at', 'decision_by', 'notes', 'metadata',
            'offer', 'student', 'decision_by_encadrant'
        ]
    
    def get_offer(self, obj):
        """Get basic offer details (local)."""
        if not obj.offer:
            return None
        
        return {
            'id': str(obj.offer.id),
            'title': obj.offer.title,
            'period_start': obj.offer.period_start,
            'period_end': obj.offer.period_end
        }
    
    def get_student(self, obj):
        """Get student details from PROFILE-SERVICE."""
        if not obj.student_id:
            return None
        
        try:
            profile_client = get_profile_client()
            student_data = profile_client.get_student_details(str(obj.student_id))
            
            if not student_data:
                return None
            
            return {
                'id': student_data.get('id'),
                'user_id': student_data.get('user_id'),
                'student_number': student_data.get('student_number'),
                'first_name': student_data.get('first_name'),
                'last_name': student_data.get('last_name'),
                'university': student_data.get('university'),
                'program': student_data.get('program'),
                'year_level': student_data.get('year_level')
            }
        except Exception as e:
            print(f"Error fetching student details: {e}")
            return None
    
    def get_decision_by_encadrant(self, obj):
        """Get encadrant (decision maker) details from AUTH-SERVICE."""
        if not obj.decision_by:
            return None
        
        try:
            auth_client = get_auth_client()
            user_data = auth_client.get_user_details(str(obj.decision_by))
            
            if not user_data:
                return None
            
            return {
                'first_name': user_data.get('first_name'),
                'last_name': user_data.get('last_name')
            }
        except Exception as e:
            print(f"Error fetching encadrant details: {e}")
            return None


class PaginatedApplications(serializers.Serializer):
    """Paginated response for applications list."""
    
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = ApplicationSerializer(many=True)
