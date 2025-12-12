"""Serializers for affectations app."""
from rest_framework import serializers
from .models import Affectation
from utils.service_client import get_profile_client
from applications.serializers import ApplicationSerializer
from offers.serializers import OfferWithDetails


class CreateAffectationRequest(serializers.Serializer):
    """Serializer for creating an affectation manually (admin only)."""
    
    application_id = serializers.UUIDField(required=True)
    student_id = serializers.UUIDField(required=True)
    offer_id = serializers.UUIDField(required=True)
    metadata = serializers.JSONField(required=False, allow_null=True)
    
    def validate_application_id(self, value):
        """Validate that application exists."""
        from applications.models import Application
        if not Application.objects.filter(id=value).exists():
            raise serializers.ValidationError('Application does not exist.')
        return value
    
    def validate_offer_id(self, value):
        """Validate that offer exists."""
        from offers.models import Offer
        if not Offer.objects.filter(id=value).exists():
            raise serializers.ValidationError('Offer does not exist.')
        return value


class AffectationSerializer(serializers.ModelSerializer):
    """Basic serializer for Affectation model."""
    
    application_id = serializers.UUIDField(source='application.id', read_only=True)
    offer_id = serializers.UUIDField(source='offer.id', read_only=True)
    
    class Meta:
        model = Affectation
        fields = [
            'id', 'application_id', 'student_id', 'offer_id',
            'assigned_at', 'metadata'
        ]
        read_only_fields = ['id', 'assigned_at']


class AffectationWithDetails(serializers.ModelSerializer):
    """Detailed serializer for Affectation with nested data."""
    
    application_id = serializers.UUIDField(source='application.id', read_only=True)
    offer_id = serializers.UUIDField(source='offer.id', read_only=True)
    
    application = serializers.SerializerMethodField()
    offer = serializers.SerializerMethodField()
    student = serializers.SerializerMethodField()
    
    class Meta:
        model = Affectation
        fields = [
            'id', 'application_id', 'student_id', 'offer_id',
            'assigned_at', 'metadata',
            'application', 'offer', 'student'
        ]
    
    def get_application(self, obj):
        """Get application data."""
        if not obj.application:
            return None
        
        return ApplicationSerializer(obj.application).data
    
    def get_offer(self, obj):
        """Get detailed offer data."""
        if not obj.offer:
            return None
        
        return OfferWithDetails(obj.offer, context=self.context).data
    
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
                'first_name': student_data.get('first_name'),
                'last_name': student_data.get('last_name'),
                'student_number': student_data.get('student_number')
            }
        except Exception as e:
            print(f"Error fetching student details: {e}")
            return None
