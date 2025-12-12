"""
ViewSets for PROFILE-SERVICE endpoints
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from .models import Establishment, Service, Student, Encadrant
from .serializers import (
    EstablishmentSerializer, ServiceSerializer,
    StudentSerializer, StudentCreateSerializer,
    EncadrantSerializer, EncadrantCreateSerializer
)
from .service_client import AuthServiceClient
from .events import publish_event, EventTypes, get_rabbitmq_client
import os
import logging

logger = logging.getLogger(__name__)

# Initialize RabbitMQ client on startup
try:
    get_rabbitmq_client(
        host=os.environ.get('RABBITMQ_HOST', 'rabbitmq'),
        port=int(os.environ.get('RABBITMQ_PORT', 5672)),
        user=os.environ.get('RABBITMQ_USER', 'admin'),
        password=os.environ.get('RABBITMQ_PASSWORD', 'password')
    )
    logger.info("✅ RabbitMQ client initialized for PROFILE-SERVICE")
except Exception as e:
    logger.warning(f"⚠️  RabbitMQ not available: {e}")


class EstablishmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Establishments (Hospitals)

    Endpoints:
    - GET    /profile/api/establishments/        - List all establishments
    - POST   /profile/api/establishments/        - Create establishment
    - GET    /profile/api/establishments/{id}/   - Get specific establishment
    - PUT    /profile/api/establishments/{id}/   - Update establishment
    - PATCH  /profile/api/establishments/{id}/   - Partial update
    - DELETE /profile/api/establishments/{id}/   - Delete establishment
    - GET    /profile/api/establishments/by_city/{city}/ - Filter by city
    """
    queryset = Establishment.objects.all()
    serializer_class = EstablishmentSerializer

    def create(self, request, *args, **kwargs):
        """Create establishment and publish establishment.created event"""
        response = super().create(request, *args, **kwargs)

        # Get created establishment
        establishment = Establishment.objects.get(id=response.data['id'])

        # Publish event
        try:
            publish_event(
                event_type=EventTypes.ESTABLISHMENT_CREATED,
                payload={
                    'establishment_id': str(establishment.id),
                    'name': establishment.name,
                    'city': establishment.city,
                    'address': establishment.address,
                    'type': establishment.type,
                    'created_at': establishment.created_at.isoformat()
                },
                service_name='profile-service'
            )
            logger.info(f"📤 Published establishment.created event for {establishment.name}")
        except Exception as e:
            logger.error(f"Failed to publish establishment.created event: {e}")

        return response

    def update(self, request, *args, **kwargs):
        """Update establishment and publish establishment.updated event"""
        response = super().update(request, *args, **kwargs)

        # Get updated establishment
        establishment = Establishment.objects.get(id=response.data['id'])

        # Publish event
        try:
            publish_event(
                event_type=EventTypes.ESTABLISHMENT_UPDATED,
                payload={
                    'establishment_id': str(establishment.id),
                    'name': establishment.name,
                    'city': establishment.city,
                    'address': establishment.address,
                    'type': establishment.type,
                    'updated_at': establishment.updated_at.isoformat()
                },
                service_name='profile-service'
            )
            logger.info(f"📤 Published establishment.updated event for {establishment.name}")
        except Exception as e:
            logger.error(f"Failed to publish establishment.updated event: {e}")

        return response

    @action(detail=False, methods=['get'], url_path='by_city/(?P<city>[^/.]+)')
    def by_city(self, request, city=None):
        """Get establishments by city"""
        establishments = self.queryset.filter(city__iexact=city)
        serializer = self.get_serializer(establishments, many=True)
        return Response(serializer.data)


class ServiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Services (Hospital Departments)

    Endpoints:
    - GET    /profile/api/services/                      - List all services
    - POST   /profile/api/services/                      - Create service
    - GET    /profile/api/services/{id}/                 - Get specific service
    - PUT    /profile/api/services/{id}/                 - Update service
    - PATCH  /profile/api/services/{id}/                 - Partial update
    - DELETE /profile/api/services/{id}/                 - Delete service
    - GET    /profile/api/services/by_establishment/{establishment_id}/ - Filter by establishment
    """
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer

    def create(self, request, *args, **kwargs):
        """Create service and publish service.created event"""
        response = super().create(request, *args, **kwargs)

        # Get created service
        service = Service.objects.get(id=response.data['id'])

        # Publish event
        try:
            publish_event(
                event_type=EventTypes.SERVICE_CREATED,
                payload={
                    'service_id': str(service.id),
                    'name': service.name,
                    'establishment_id': str(service.establishment_id),
                    'type': service.type,
                    'created_at': service.created_at.isoformat()
                },
                service_name='profile-service'
            )
            logger.info(f"📤 Published service.created event for {service.name}")
        except Exception as e:
            logger.error(f"Failed to publish service.created event: {e}")

        return response

    def update(self, request, *args, **kwargs):
        """Update service and publish service.updated event"""
        response = super().update(request, *args, **kwargs)

        # Get updated service
        service = Service.objects.get(id=response.data['id'])

        # Publish event
        try:
            publish_event(
                event_type=EventTypes.SERVICE_UPDATED,
                payload={
                    'service_id': str(service.id),
                    'name': service.name,
                    'establishment_id': str(service.establishment_id),
                    'type': service.type,
                    'updated_at': service.updated_at.isoformat()
                },
                service_name='profile-service'
            )
            logger.info(f"📤 Published service.updated event for {service.name}")
        except Exception as e:
            logger.error(f"Failed to publish service.updated event: {e}")

        return response

    @action(detail=False, methods=['get'], url_path='by_establishment/(?P<establishment_id>[^/.]+)')
    def by_establishment(self, request, establishment_id=None):
        """Get services by establishment"""
        services = self.queryset.filter(establishment_id=establishment_id)
        serializer = self.get_serializer(services, many=True)
        return Response(serializer.data)


class StudentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Students

    Endpoints:
    - GET    /profile/api/students/                - List all students
    - POST   /profile/api/students/                - Create student
    - GET    /profile/api/students/{id}/           - Get specific student
    - PUT    /profile/api/students/{id}/           - Update student
    - PATCH  /profile/api/students/{id}/           - Partial update
    - DELETE /profile/api/students/{id}/           - Delete student
    - GET    /profile/api/students/by_user/{user_id}/ - Get by user_id
    """
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return StudentCreateSerializer
        return StudentSerializer

    def create(self, request, *args, **kwargs):
        """Create student and publish student.created event"""
        response = super().create(request, *args, **kwargs)

        # Get created student
        student = Student.objects.get(id=response.data['id'])

        # Publish event
        try:
            publish_event(
                event_type=EventTypes.STUDENT_CREATED,
                payload={
                    'student_id': str(student.id),
                    'user_id': str(student.user_id),
                    'cin': student.cin,
                    'email': student.email,
                    'phone': student.phone,
                    'first_name': student.first_name,
                    'last_name': student.last_name,
                    'created_at': student.created_at.isoformat()
                },
                service_name='profile-service'
            )
            logger.info(f"📤 Published student.created event for student {student.id}")
        except Exception as e:
            logger.error(f"Failed to publish student.created event: {e}")

        return response

    def update(self, request, *args, **kwargs):
        """Update student and publish student.updated event"""
        # Track which fields are being updated
        instance = self.get_object()
        old_data = {
            'cin': instance.cin,
            'email': instance.email,
            'phone': instance.phone,
            'first_name': instance.first_name,
            'last_name': instance.last_name
        }

        response = super().update(request, *args, **kwargs)

        # Get updated student
        student = Student.objects.get(id=response.data['id'])

        # Determine which fields changed
        updated_fields = []
        new_data = {
            'cin': student.cin,
            'email': student.email,
            'phone': student.phone,
            'first_name': student.first_name,
            'last_name': student.last_name
        }
        for field, old_value in old_data.items():
            if old_value != new_data[field]:
                updated_fields.append(field)

        # Publish event
        try:
            publish_event(
                event_type=EventTypes.STUDENT_UPDATED,
                payload={
                    'student_id': str(student.id),
                    'user_id': str(student.user_id),
                    'updated_fields': updated_fields,
                    'cin': student.cin,
                    'email': student.email,
                    'phone': student.phone,
                    'first_name': student.first_name,
                    'last_name': student.last_name,
                    'updated_at': student.updated_at.isoformat()
                },
                service_name='profile-service'
            )
            logger.info(f"📤 Published student.updated event for student {student.id}")
        except Exception as e:
            logger.error(f"Failed to publish student.updated event: {e}")

        return response

    def destroy(self, request, *args, **kwargs):
        """Delete student and publish student.deleted event"""
        instance = self.get_object()

        # Store data before deletion
        student_data = {
            'student_id': str(instance.id),
            'user_id': str(instance.user_id),
            'cin': instance.cin,
            'email': instance.email
        }

        response = super().destroy(request, *args, **kwargs)

        # Publish event
        try:
            publish_event(
                event_type=EventTypes.STUDENT_DELETED,
                payload=student_data,
                service_name='profile-service'
            )
            logger.info(f"📤 Published student.deleted event for student {student_data['student_id']}")
        except Exception as e:
            logger.error(f"Failed to publish student.deleted event: {e}")

        return response

    @action(detail=False, methods=['get'], url_path='by_user/(?P<user_id>[^/.]+)')
    def by_user(self, request, user_id=None):
        """Get student by user_id (includes user data from AUTH-SERVICE)"""
        try:
            student = self.queryset.get(user_id=user_id)
            serializer = StudentSerializer(student)
            return Response(serializer.data)
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class EncadrantViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Encadrants (Supervisors/Mentors)

    Endpoints:
    - GET    /profile/api/encadrants/                      - List all encadrants
    - POST   /profile/api/encadrants/                      - Create encadrant
    - GET    /profile/api/encadrants/{id}/                 - Get specific encadrant
    - PUT    /profile/api/encadrants/{id}/                 - Update encadrant
    - PATCH  /profile/api/encadrants/{id}/                 - Partial update
    - DELETE /profile/api/encadrants/{id}/                 - Delete encadrant
    - GET    /profile/api/encadrants/by_user/{user_id}/    - Get by user_id
    - GET    /profile/api/encadrants/by_establishment/{establishment_id}/ - Filter by establishment
    """
    queryset = Encadrant.objects.all()
    serializer_class = EncadrantSerializer

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return EncadrantCreateSerializer
        return EncadrantSerializer

    def create(self, request, *args, **kwargs):
        """Create encadrant and publish encadrant.created event"""
        response = super().create(request, *args, **kwargs)

        # Get created encadrant
        encadrant = Encadrant.objects.get(id=response.data['id'])

        # Publish event
        try:
            publish_event(
                event_type=EventTypes.ENCADRANT_CREATED,
                payload={
                    'encadrant_id': str(encadrant.id),
                    'user_id': str(encadrant.user_id),
                    'cin': encadrant.cin,
                    'email': encadrant.email,
                    'phone': encadrant.phone,
                    'first_name': encadrant.first_name,
                    'last_name': encadrant.last_name,
                    'establishment_id': str(encadrant.establishment_id) if encadrant.establishment_id else None,
                    'service_id': str(encadrant.service_id) if encadrant.service_id else None,
                    'speciality': encadrant.speciality,
                    'created_at': encadrant.created_at.isoformat()
                },
                service_name='profile-service'
            )
            logger.info(f"📤 Published encadrant.created event for encadrant {encadrant.id}")
        except Exception as e:
            logger.error(f"Failed to publish encadrant.created event: {e}")

        return response

    def update(self, request, *args, **kwargs):
        """Update encadrant and publish encadrant.updated event"""
        # Track which fields are being updated
        instance = self.get_object()
        old_data = {
            'cin': instance.cin,
            'email': instance.email,
            'phone': instance.phone,
            'first_name': instance.first_name,
            'last_name': instance.last_name,
            'speciality': instance.speciality,
            'establishment_id': str(instance.establishment_id) if instance.establishment_id else None,
            'service_id': str(instance.service_id) if instance.service_id else None
        }

        response = super().update(request, *args, **kwargs)

        # Get updated encadrant
        encadrant = Encadrant.objects.get(id=response.data['id'])

        # Determine which fields changed
        updated_fields = []
        new_data = {
            'cin': encadrant.cin,
            'email': encadrant.email,
            'phone': encadrant.phone,
            'first_name': encadrant.first_name,
            'last_name': encadrant.last_name,
            'speciality': encadrant.speciality,
            'establishment_id': str(encadrant.establishment_id) if encadrant.establishment_id else None,
            'service_id': str(encadrant.service_id) if encadrant.service_id else None
        }
        for field, old_value in old_data.items():
            if old_value != new_data[field]:
                updated_fields.append(field)

        # Publish event
        try:
            publish_event(
                event_type=EventTypes.ENCADRANT_UPDATED,
                payload={
                    'encadrant_id': str(encadrant.id),
                    'user_id': str(encadrant.user_id),
                    'updated_fields': updated_fields,
                    'cin': encadrant.cin,
                    'email': encadrant.email,
                    'phone': encadrant.phone,
                    'first_name': encadrant.first_name,
                    'last_name': encadrant.last_name,
                    'establishment_id': str(encadrant.establishment_id) if encadrant.establishment_id else None,
                    'service_id': str(encadrant.service_id) if encadrant.service_id else None,
                    'speciality': encadrant.speciality,
                    'updated_at': encadrant.updated_at.isoformat()
                },
                service_name='profile-service'
            )
            logger.info(f"📤 Published encadrant.updated event for encadrant {encadrant.id}")
        except Exception as e:
            logger.error(f"Failed to publish encadrant.updated event: {e}")

        return response

    def destroy(self, request, *args, **kwargs):
        """Delete encadrant and publish encadrant.deleted event"""
        instance = self.get_object()

        # Store data before deletion
        encadrant_data = {
            'encadrant_id': str(instance.id),
            'user_id': str(instance.user_id),
            'cin': instance.cin,
            'email': instance.email
        }

        response = super().destroy(request, *args, **kwargs)

        # Publish event
        try:
            publish_event(
                event_type=EventTypes.ENCADRANT_DELETED,
                payload=encadrant_data,
                service_name='profile-service'
            )
            logger.info(f"📤 Published encadrant.deleted event for encadrant {encadrant_data['encadrant_id']}")
        except Exception as e:
            logger.error(f"Failed to publish encadrant.deleted event: {e}")

        return response

    @action(detail=False, methods=['get'], url_path='by_user/(?P<user_id>[^/.]+)')
    def by_user(self, request, user_id=None):
        """Get encadrant by user_id (includes user data from AUTH-SERVICE)"""
        try:
            encadrant = self.queryset.get(user_id=user_id)
            serializer = EncadrantSerializer(encadrant)
            return Response(serializer.data)
        except Encadrant.DoesNotExist:
            return Response(
                {'error': 'Encadrant not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'], url_path='by_establishment/(?P<establishment_id>[^/.]+)')
    def by_establishment(self, request, establishment_id=None):
        """Get encadrants by establishment"""
        encadrants = self.queryset.filter(establishment_id=establishment_id)
        serializer = self.get_serializer(encadrants, many=True)
        return Response(serializer.data)


@api_view(['GET'])
def get_my_profile(request):
    """
    Get current user's profile based on their role

    Endpoint: GET /profile/me

    This endpoint:
    1. Gets user_id from request headers (X-User-ID) or query params
    2. Fetches user data from AUTH-SERVICE to determine role
    3. Returns student or encadrant profile based on role
    """
    # Get user_id from headers or query params (mock for now)
    user_id = request.headers.get('X-User-ID') or request.query_params.get('user_id')

    if not user_id:
        return Response(
            {'error': 'user_id required in X-User-ID header or user_id query param'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Get user data from AUTH-SERVICE to determine role
    user_data = AuthServiceClient.get_user_by_id(user_id)

    if not user_data:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    user_role = user_data.get('role', 'student')

    # Based on role, get the appropriate profile
    if user_role == 'student':
        try:
            student = Student.objects.get(user_id=user_id)
            serializer = StudentSerializer(student)
            return Response(serializer.data)
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student profile not found', 'user_role': user_role},
                status=status.HTTP_404_NOT_FOUND
            )

    elif user_role == 'encadrant':
        try:
            encadrant = Encadrant.objects.get(user_id=user_id)
            serializer = EncadrantSerializer(encadrant)
            return Response(serializer.data)
        except Encadrant.DoesNotExist:
            return Response(
                {'error': 'Encadrant profile not found', 'user_role': user_role},
                status=status.HTTP_404_NOT_FOUND
            )

    else:
        return Response(
            {'error': f'No profile type for role: {user_role}'},
            status=status.HTTP_400_BAD_REQUEST
        )