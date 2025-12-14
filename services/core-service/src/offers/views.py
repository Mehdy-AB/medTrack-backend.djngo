"""Views for offers app."""
import jwt
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters import rest_framework as filters
from .models import Offer
from .serializers import (
    OfferSerializer, OfferListSerializer, CreateOfferRequest,
    UpdateOfferRequest, OfferWithDetails
)
from utils.event_publisher import get_event_publisher


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


class OfferPagination(PageNumberPagination):
    """Custom pagination for offers."""
    page_size = 20
    page_size_query_param = 'per_page'
    max_page_size = 100
    page_query_param = 'page'


class OfferFilter(filters.FilterSet):
    """Filter for offers."""
    status = filters.CharFilter(field_name='status')
    service_id = filters.UUIDFilter(field_name='service_id')
    establishment_id = filters.UUIDFilter(field_name='establishment_id')
    created_by = filters.UUIDFilter(field_name='created_by')
    active_only = filters.BooleanFilter(method='filter_active_only')
    search = filters.CharFilter(method='filter_search')
    
    class Meta:
        model = Offer
        fields = ['status', 'service_id', 'establishment_id', 'created_by', 'active_only', 'search']
    
    def filter_active_only(self, queryset, name, value):
        """Filter for active offers (published and not ended)."""
        if value:
            today = timezone.now().date()
            return queryset.filter(
                status=Offer.STATUS_PUBLISHED
            ).filter(
                Q(period_end__isnull=True) | Q(period_end__gte=today)
            )
        return queryset
    
    def filter_search(self, queryset, name, value):
        """Search in title and description."""
        if value:
            return queryset.filter(
                Q(title__icontains=value) | Q(description__icontains=value)
            )
        return queryset


class OfferViewSet(viewsets.ModelViewSet):
    """ViewSet for Offer model."""
    queryset = Offer.objects.all()
    serializer_class = OfferSerializer
    filterset_class = OfferFilter
    pagination_class = OfferPagination
    
    def get_serializer_class(self):
        """Use appropriate serializer for each action."""
        if self.action == 'list':
            return OfferListSerializer
        elif self.action == 'retrieve':
            return OfferWithDetails
        elif self.action == 'create':
            return CreateOfferRequest
        elif self.action in ['update', 'partial_update']:
            return UpdateOfferRequest
        return OfferSerializer
    
    def create(self, request):
        """Create a new internship offer."""
        serializer = CreateOfferRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_id = get_user_id_from_request(request)
        
        offer = Offer.objects.create(
            title=serializer.validated_data['title'],
            description=serializer.validated_data['description'],
            service_id=serializer.validated_data['service_id'],
            establishment_id=serializer.validated_data.get('establishment_id'),
            period_start=serializer.validated_data.get('period_start'),
            period_end=serializer.validated_data.get('period_end'),
            created_by=user_id,
            status='draft'
        )
        
        # Publish offer.created event
        publisher = get_event_publisher()
        publisher.publish_offer_created({
            'offer_id': str(offer.id),
            'title': offer.title,
            'service_id': str(offer.service_id),
            'establishment_id': str(offer.establishment_id) if offer.establishment_id else None,
            'created_by': str(user_id) if user_id else None,
            'status': offer.status
        })
        
        return Response(
            OfferSerializer(offer).data,
            status=status.HTTP_201_CREATED
        )
    
    # The perform_create method is no longer needed as the custom create method handles it.
    # def perform_create(self, serializer):
    #     """Set created_by from JWT token."""
    #     user_id = get_user_id_from_request(self.request)
    #     serializer.save(created_by=user_id)
    
    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, pk=None):
        """Update offer status."""
        offer = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status:
            return Response(
                {'error': 'status field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if new_status not in dict(Offer.STATUS_CHOICES):
            return Response(
                {'error': f'Invalid status. Must be one of: {", ".join([s[0] for s in Offer.STATUS_CHOICES])}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = offer.status
        offer.status = new_status
        offer.save()
        
        # Publish appropriate event based on new status
        publisher = get_event_publisher()
        event_data = {
            'offer_id': str(offer.id),
            'title': offer.title,
            'status': new_status,
            'old_status': old_status
        }
        
        if new_status == 'published':
            publisher.publish_offer_published(event_data)
        elif new_status == 'closed':
            publisher.publish_offer_closed(event_data)
        else:
            publisher.publish_offer_updated(event_data)
        
        serializer = OfferSerializer(offer)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='applications')
    def list_applications(self, request, pk=None):
        """Get applications for this offer."""
        from applications.models import Application
        from applications.serializers import ApplicationSerializer
        
        offer = self.get_object()
        applications = Application.objects.filter(offer=offer)
        
        # Filter by status if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            applications = applications.filter(status=status_filter)
        
        # Pagination
        page = request.query_params.get('page', 1)
        per_page = request.query_params.get('per_page', 20)
        
        try:
            page = int(page)
            per_page = min(int(per_page), 100)  # Max 100 per page
        except (ValueError, TypeError):
            page = 1
            per_page = 20
        
        # Manual pagination
        start = (page - 1) * per_page
        end = start + per_page
        total_count = applications.count()
        
        applications_page = applications[start:end]
        
        serializer = ApplicationSerializer(applications_page, many=True)
        
        # Build pagination response
        base_url = request.build_absolute_uri().split('?')[0]
        next_url = None
        prev_url = None
        
        if end < total_count:
            next_url = f"{base_url}?page={page + 1}&per_page={per_page}"
            if status_filter:
                next_url += f"&status={status_filter}"
        
        if page > 1:
            prev_url = f"{base_url}?page={page - 1}&per_page={per_page}"
            if status_filter:
                prev_url += f"&status={status_filter}"
        
        return Response({
            'count': total_count,
            'next': next_url,
            'previous': prev_url,
            'results': serializer.data
        })
