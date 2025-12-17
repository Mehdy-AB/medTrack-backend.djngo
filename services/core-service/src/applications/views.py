"""Views for applications app."""
import jwt
from django.conf import settings
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters import rest_framework as filters
from .models import Application
from .serializers import (
    ApplicationSerializer, ApplicationWithDetails,
    CreateApplicationRequest, UpdateApplicationRequest,
    UpdateApplicationStatusRequest
)
from offers.models import Offer
from utils.event_publisher import get_event_publisher
from utils.rbac import get_user_role, get_user_id


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


class ApplicationPagination(PageNumberPagination):
    """Custom pagination for applications."""
    page_size = 20
    page_size_query_param = 'per_page'
    max_page_size = 100
    page_query_param = 'page'


class ApplicationFilter(filters.FilterSet):
    """Filter for applications."""
    student_id = filters.UUIDFilter(field_name='student_id')
    offer_id = filters.UUIDFilter(field_name='offer__id')
    status = filters.CharFilter(field_name='status')
    
    class Meta:
        model = Application
        fields = ['student_id', 'offer_id', 'status']


class ApplicationViewSet(viewsets.ModelViewSet):
    """ViewSet for Application model."""
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    filterset_class = ApplicationFilter
    pagination_class = ApplicationPagination
    
    def get_serializer_class(self):
        """Use appropriate serializer for each action."""
        if self.action == 'retrieve':
            return ApplicationWithDetails
        elif self.action == 'create':
            return CreateApplicationRequest
        elif self.action in ['update', 'partial_update']:
            return UpdateApplicationRequest
        return ApplicationSerializer
    
    def create(self, request):
        """Create a new application."""
        serializer = CreateApplicationRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_id = get_user_id_from_request(request)
        
        # Verify offer exists and is active
        try:
            offer = Offer.objects.get(id=serializer.validated_data['offer_id'])
            if offer.status != Offer.STATUS_PUBLISHED:
                return Response(
                    {'error': 'This offer is not currently accepting applications'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Offer.DoesNotExist:
            return Response(
                {'error': 'Offer not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create application
        application = Application.objects.create(
            student_id=serializer.validated_data['student_id'],
            offer=offer,
            status=Application.STATUS_SUBMITTED,
            metadata={
                'motivation': serializer.validated_data.get('motivation'),
                'document_ids': serializer.validated_data.get('document_ids', [])
            }
        )
        
        # Publish application.submitted event
        publisher = get_event_publisher()
        publisher.publish_application_submitted({
            'application_id': str(application.id),
            'student_id': str(application.student_id),
            'offer_id': str(offer.id),
            'offer_title': offer.title,
            'status': application.status,
            'submitted_at': application.submitted_at.isoformat()
        })
        
        return Response(
            ApplicationSerializer(application).data,
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """Update application (student only can update their own)."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Check if student owns this application
        user_id = get_user_id_from_request(request)
        if str(instance.student_id) != str(user_id):
            return Response(
                {'error': 'You can only update your own applications'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Can't update if already decided
        if instance.status in [Application.STATUS_ACCEPTED, Application.STATUS_REJECTED]:
            return Response(
                {'error': 'Cannot update application that has been decided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Update metadata
        if instance.metadata is None:
            instance.metadata = {}
        
        if 'motivation' in serializer.validated_data:
            instance.metadata['motivation'] = serializer.validated_data['motivation']
        if 'document_ids' in serializer.validated_data:
            instance.metadata['document_ids'] = serializer.validated_data['document_ids']
        
        instance.save()
        
        # Publish application.updated event
        publisher = get_event_publisher()
        publisher.publish_application_updated({
            'application_id': str(instance.id),
            'student_id': str(instance.student_id),
            'offer_id': str(instance.offer.id),
            'offer_title': instance.offer.title,
            'status': instance.status,
            'updated_at': timezone.now().isoformat()
        })
        
        response_serializer = ApplicationSerializer(instance)
        return Response(response_serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """Cancel application (student only)."""
        application = self.get_object()
        user_id = get_user_id_from_request(request)
        
        # Check if student owns this application
        if str(application.student_id) != str(user_id):
            return Response(
                {'error': 'You can only cancel your own applications'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Can't cancel if accepted
        if application.status == Application.STATUS_ACCEPTED:
            return Response(
                {'error': 'Cannot cancel an accepted application'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Publish application.withdrawn event before status change
        publisher = get_event_publisher()
        publisher.publish_application_withdrawn({
            'application_id': str(application.id),
            'student_id': str(application.student_id),
            'offer_id': str(application.offer.id),
            'offer_title': application.offer.title,
            'withdrawn_at': timezone.now().isoformat()
        })
        
        # Set status to cancelled instead of deleting
        application.status = Application.STATUS_CANCELLED
        application.save()
        
        return Response(
            {'message': 'Application cancelled successfully'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, pk=None):
        """Update application status (encadrant/admin only)."""
        # Only encadrants and admins can accept/reject applications
        role = get_user_role(request)
        if role not in ['encadrant', 'admin']:
            return Response(
                {' error': 'Only encadrants and admins can accept/reject applications',
                    'required_roles': ['encadrant', 'admin'],
                    'your_role': role
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        application = self.get_object()
        user_id = get_user_id(request)
        
        serializer = UpdateApplicationStatusRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_status = serializer.validated_data['status']
        
        # Validate status transition
        if application.status == Application.STATUS_ACCEPTED:
            return Response(
                {'error': 'Cannot change status of an already accepted application'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check available slots if accepting
        if new_status == 'accepted':
            if not application.offer.has_available_slots():
                return Response(
                    {'error': 'No available slots for this offer'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Update application
        application.status = new_status
        application.decision_at = timezone.now()
        application.decision_by = user_id
        
        if 'notes' in serializer.validated_data:
            application.notes = serializer.validated_data['notes']
        
        application.save()
        
        # Publish event based on status
        publisher = get_event_publisher()
        
        if application.status == Application.STATUS_ACCEPTED:
            publisher.publish_application_accepted({
                'application_id': str(application.id),
                'student_id': str(application.student_id),
                'offer_id': str(application.offer.id),
                'offer_title': application.offer.title,
                'decision_by': str(user_id) if user_id else None,
                'decision_at': application.decision_at.isoformat() if application.decision_at else None
            })
        elif application.status == Application.STATUS_REJECTED:
            publisher.publish_application_rejected({
                'application_id': str(application.id),
                'student_id': str(application.student_id),
                'offer_id': str(application.offer.id),
                'decision_by': str(user_id) if user_id else None,
                'notes': application.notes
            })
        
        # Create affectation if accepted
        if application.status == Application.STATUS_ACCEPTED:
            from affectations.models import Affectation
            Affectation.objects.get_or_create(
                application=application,
                defaults={
                    'student_id': application.student_id,
                    'offer': application.offer
                }
            )
        
        response_serializer = ApplicationSerializer(application)
        return Response(response_serializer.data)
