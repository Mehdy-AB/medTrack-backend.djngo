"""Serializers for offers app."""
from rest_framework import serializers
from .models import Offer
from utils.service_client import get_auth_client, get_profile_client


class CreateOfferRequest(serializers.ModelSerializer):
    """Serializer for creating a new offer."""
    
    status = serializers.ChoiceField(
        choices=Offer.STATUS_CHOICES,
        default=Offer.STATUS_DRAFT,
        required=False
    )
    
    class Meta:
        model = Offer
        fields = [
            'title', 'description', 'service_id', 'establishment_id',
            'period_start', 'period_end', 'available_slots', 'status', 'metadata'
        ]
    
    def validate_title(self, value):
        """Validate title length."""
        if len(value) < 5:
            raise serializers.ValidationError('Title must be at least 5 characters long.')
        if len(value) > 255:
            raise serializers.ValidationError('Title must be at most 255 characters long.')
        return value
    
    def validate(self, data):
        """Validate offer data."""
        period_start = data.get('period_start')
        period_end = data.get('period_end')
        
        if period_start and period_end and period_start > period_end:
            raise serializers.ValidationError({
                'period_end': 'End date must be after start date.'
            })
        
        available_slots = data.get('available_slots', 1)
        if available_slots < 1:
            raise serializers.ValidationError({
                'available_slots': 'Available slots must be at least 1.'
            })
        
        return data


class UpdateOfferRequest(serializers.ModelSerializer):
    """Serializer for updating an offer (all fields optional)."""
    
    status = serializers.ChoiceField(
        choices=Offer.STATUS_CHOICES,
        required=False
    )
    
    class Meta:
        model = Offer
        fields = [
            'title', 'description', 'service_id', 'establishment_id',
            'period_start', 'period_end', 'available_slots', 'status', 'metadata'
        ]
        extra_kwargs = {
            'title': {'required': False},
            'service_id': {'required': False},
        }
    
    def validate_title(self, value):
        """Validate title length."""
        if value and len(value) < 5:
            raise serializers.ValidationError('Title must be at least 5 characters long.')
        if value and len(value) > 255:
            raise serializers.ValidationError('Title must be at most 255 characters long.')
        return value
    
    def validate(self, data):
        """Validate offer data."""
        # Get current instance values for fields not in update
        instance = self.instance
        period_start = data.get('period_start', instance.period_start if instance else None)
        period_end = data.get('period_end', instance.period_end if instance else None)
        
        if period_start and period_end and period_start > period_end:
            raise serializers.ValidationError({
                'period_end': 'End date must be after start date.'
            })
        
        available_slots = data.get('available_slots')
        if available_slots is not None and available_slots < 1:
            raise serializers.ValidationError({
                'available_slots': 'Available slots must be at least 1.'
            })
        
        return data


class OfferSerializer(serializers.ModelSerializer):
    """Serializer for Offer model."""
    
    class Meta:
        model = Offer
        fields = [
            'id', 'title', 'description', 'service_id', 'establishment_id',
            'created_by', 'period_start', 'period_end', 'available_slots',
            'status', 'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    def validate(self, data):
        """Validate offer data."""
        period_start = data.get('period_start')
        period_end = data.get('period_end')
        
        if period_start and period_end and period_start > period_end:
            raise serializers.ValidationError({
                'period_end': 'End date must be after start date.'
            })
        
        available_slots = data.get('available_slots')
        if available_slots is not None and available_slots < 0:
            raise serializers.ValidationError({
                'available_slots': 'Available slots cannot be negative.'
            })
        
        return data


class OfferListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing offers."""
    
    accepted_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Offer
        fields = [
            'id', 'title', 'service_id', 'period_start', 'period_end',
            'available_slots', 'accepted_count', 'status', 'created_at'
        ]
    
    def get_accepted_count(self, obj):
        """Get count of accepted applications."""
        return obj.get_accepted_count()


class OfferWithDetails(serializers.ModelSerializer):
    """Detailed serializer for single offer retrieval with nested data."""
    
    service = serializers.SerializerMethodField()
    created_by_encadrant = serializers.SerializerMethodField()
    application_count = serializers.SerializerMethodField()
    remaining_slots = serializers.SerializerMethodField()
    
    class Meta:
        model = Offer
        fields = [
            'id', 'title', 'description', 'service_id', 'establishment_id',
            'created_by', 'period_start', 'period_end', 'available_slots',
            'status', 'metadata', 'created_at', 'updated_at',
            'service', 'created_by_encadrant', 'application_count', 'remaining_slots'
        ]
    
    def get_service(self, obj):
        """Get service details from PROFILE-SERVICE."""
        if not obj.service_id:
            return None
        
        try:
            profile_client = get_profile_client()
            service_data = profile_client.get_service_details(str(obj.service_id))
            
            if not service_data:
                return {
                    'id': str(obj.service_id),
                    'name': None,
                    'establishment': None
                }
            
            # Get establishment details if available
            establishment = None
            establishment_id = service_data.get('establishment_id') or obj.establishment_id
            
            if establishment_id:
                est_data = profile_client.get_establishment_details(str(establishment_id))
                
                if est_data:
                    establishment = {
                        'id': est_data.get('id'),
                        'name': est_data.get('name'),
                        'city': est_data.get('city')
                    }
            
            return {
                'id': service_data.get('id'),
                'name': service_data.get('name'),
                'establishment': establishment
            }
        except Exception as e:
            print(f"Error fetching service details: {e}")
            return {
                'id': str(obj.service_id),
                'name': None,
                'establishment': None
            }
    
    def get_created_by_encadrant(self, obj):
        """Get user (encadrant) details from AUTH-SERVICE."""
        if not obj.created_by:
            return None
        
        try:
            auth_client = get_auth_client()
            user_data = auth_client.get_user_details(str(obj.created_by))
            
            if not user_data:
                return None
            
            return {
                'id': user_data.get('id'),
                'first_name': user_data.get('first_name'),
                'last_name': user_data.get('last_name')
            }
        except Exception as e:
            print(f"Error fetching user details: {e}")
            return None
    
    def get_application_count(self, obj):
        """Get total count of applications."""
        return obj.applications.count()
    
    def get_remaining_slots(self, obj):
        """Calculate remaining available slots."""
        accepted_count = obj.get_accepted_count()
        return max(0, obj.available_slots - accepted_count)


class PaginatedOffers(serializers.Serializer):
    """Paginated response for offers list."""
    
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = OfferListSerializer(many=True)
