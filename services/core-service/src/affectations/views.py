"""Views for affectations app."""
import jwt
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters import rest_framework as filters
from .models import Affectation
from .serializers import (
    AffectationSerializer, AffectationWithDetails,
    CreateAffectationRequest
)
from applications.models import Application
from offers.models import Offer


def get_user_id_from_request(request):
    """Extract user_id from JWT token in Authorization header."""
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header:
        return None
    
    try:
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None
        
        token = parts[1]
        secret_key = getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)
        algorithm = getattr(settings, 'JWT_ALGORITHM', 'HS256')
        
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[algorithm],
            options={"verify_signature": True}
        )
        
        return payload.get('user_id') or payload.get('sub') or payload.get('id')
    except:
        return None


class AffectationPagination(PageNumberPagination):
    """Custom pagination for affectations."""
    page_size = 20
    page_size_query_param = 'per_page'
    max_page_size = 100
    page_query_param = 'page'


class AffectationFilter(filters.FilterSet):
    """Filter for affectations."""
    student_id = filters.UUIDFilter(field_name='student_id')
    offer_id = filters.UUIDFilter(field_name='offer__id')
    active_only = filters.BooleanFilter(method='filter_active_only')
    
    class Meta:
        model = Affectation
        fields = ['student_id', 'offer_id', 'active_only']
    
    def filter_active_only(self, queryset, name, value):
        """Filter for active affectations (where offer is still active)."""
        if value:
            from django.utils import timezone
            from django.db import models
            today = timezone.now().date()
            
            # Active = offer is published and not ended
            return queryset.filter(
                offer__status='published'
            ).filter(
                models.Q(offer__period_end__isnull=True) | 
                models.Q(offer__period_end__gte=today)
            )
        return queryset


class AffectationViewSet(viewsets.ModelViewSet):
    """ViewSet for Affectation model."""
    queryset = Affectation.objects.all()
    serializer_class = AffectationSerializer
    filterset_class = AffectationFilter
    pagination_class = AffectationPagination
    
    def get_serializer_class(self):
        """Use detailed serializer for retrieve and list."""
        if self.action in ['retrieve', 'list', 'by_student']:
            return AffectationWithDetails
        elif self.action == 'create':
            return CreateAffectationRequest
        return AffectationSerializer
    
    def create(self, request, *args, **kwargs):
        """Create affectation manually (admin only)."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get related objects
        application = Application.objects.get(id=serializer.validated_data['application_id'])
        offer = Offer.objects.get(id=serializer.validated_data['offer_id'])
        
        # Check if affectation already exists for this application
        if Affectation.objects.filter(application=application).exists():
            return Response(
                {'error': 'Affectation already exists for this application'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create affectation
        affectation = Affectation.objects.create(
            application=application,
            student_id=serializer.validated_data['student_id'],
            offer=offer,
            metadata=serializer.validated_data.get('metadata')
        )
        
        # Return with detailed serializer
        response_serializer = AffectationWithDetails(affectation)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def destroy(self, request, *args, **kwargs):
        """Delete affectation."""
        affectation = self.get_object()
        affectation.delete()
        
        return Response(
            {
                'success': True,
                'message': 'Affectation deleted successfully'
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'], url_path='by-student/(?P<student_id>[^/.]+)')
    def by_student(self, request, student_id=None):
        """Get affectations for a specific student."""
        queryset = self.queryset.filter(student_id=student_id)
        
        # Apply active_only filter if provided
        active_only = request.query_params.get('active_only', 'false').lower() == 'true'
        if active_only:
            from django.utils import timezone
            from django.db import models
            today = timezone.now().date()
            
            queryset = queryset.filter(
                offer__status=Offer.STATUS_PUBLISHED
            ).filter(
                models.Q(offer__period_end__isnull=True) | 
                models.Q(offer__period_end__gte=today)
            )
        
        serializer = AffectationWithDetails(queryset, many=True)
        return Response(serializer.data)
