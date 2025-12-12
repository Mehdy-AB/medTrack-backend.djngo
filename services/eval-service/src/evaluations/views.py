"""Views for evaluations app."""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from .models import Evaluation, EvaluationSection
from .serializers import (
    EvaluationSerializer,
    EvaluationWithDetailsSerializer,
    CreateEvaluationRequest,
    UpdateEvaluationRequest,
    ValidateEvaluationRequest,
    EvaluationSectionSerializer,
    CreateEvaluationSectionRequest,
    PaginatedEvaluations
)


def get_user_id_from_request(request):
    """Extract user ID from JWT token."""
    import jwt
    import os
    
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        try:
            secret_key = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
            algorithm = os.environ.get('JWT_ALGORITHM', 'HS256')
            payload = jwt.decode(token, secret_key, algorithms=[algorithm])
            return payload.get('user_id') or payload.get('sub')
        except Exception as e:
            print(f"Error decoding JWT: {e}")
    return None


class EvaluationPagination(PageNumberPagination):
    """Pagination for evaluations."""
    page_size = 20
    page_size_query_param = 'per_page'
    max_page_size = 100


class EvaluationViewSet(viewsets.ModelViewSet):
    """ViewSet for evaluations."""
    queryset = Evaluation.objects.all()
    serializer_class = EvaluationSerializer
    pagination_class = EvaluationPagination
    
    def get_serializer_class(self):
        """Use detailed serializer for list/retrieve."""
        if self.action in ['list', 'retrieve']:
            return EvaluationWithDetailsSerializer
        return EvaluationSerializer
    
    def get_queryset(self):
        """Filter evaluations based on query parameters."""
        queryset = Evaluation.objects.all()
        
        # Filters
        student_id = self.request.query_params.get('student_id')
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        
        offer_id = self.request.query_params.get('offer_id')
        if offer_id:
            queryset = queryset.filter(offer_id=offer_id)
        
        evaluator_id = self.request.query_params.get('evaluator_id')
        if evaluator_id:
            queryset = queryset.filter(evaluator_id=evaluator_id)
        
        validated = self.request.query_params.get('validated')
        if validated is not None:
            queryset = queryset.filter(validated=validated.lower() == 'true')
        
        return queryset.order_by('-submitted_at')
    
    def create(self, request):
        """Create new evaluation with optional sections."""
        serializer = CreateEvaluationRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_id = get_user_id_from_request(request)
        
        # Create evaluation
        evaluation = Evaluation.objects.create(
            student_id=serializer.validated_data['student_id'],
            offer_id=serializer.validated_data['offer_id'],
            evaluator_id=user_id or serializer.validated_data.get('evaluator_id'),
            grade=serializer.validated_data.get('grade'),
            comments=serializer.validated_data.get('comments'),
        )
        
        # Create sections if provided
        sections_data = serializer.validated_data.get('sections', [])
        for section_data in sections_data:
            EvaluationSection.objects.create(
                evaluation=evaluation,
                criterion=section_data['criterion'],
                score=section_data.get('score'),
                comments=section_data.get('comments'),
            )
        
        response_serializer = EvaluationSerializer(evaluation)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, pk=None):
        """Update evaluation and optionally update sections."""
        evaluation = self.get_object()
        serializer = UpdateEvaluationRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Update evaluation fields
        if 'grade' in serializer.validated_data:
            evaluation.grade = serializer.validated_data['grade']
        if 'comments' in serializer.validated_data:
            evaluation.comments = serializer.validated_data['comments']
        
        evaluation.save()
        
        # Update sections if provided
        sections_data = serializer.validated_data.get('sections', [])
        for section_data in sections_data:
            section_id = section_data.get('id')
            if section_id:
                # Update existing section
                try:
                    section = EvaluationSection.objects.get(id=section_id, evaluation=evaluation)
                    if 'criterion' in section_data:
                        section.criterion = section_data['criterion']
                    if 'score' in section_data:
                        section.score = section_data['score']
                    if 'comments' in section_data:
                        section.comments = section_data['comments']
                    section.save()
                except EvaluationSection.DoesNotExist:
                    pass
            else:
                # Create new section
                if 'criterion' in section_data:
                    EvaluationSection.objects.create(
                        evaluation=evaluation,
                        criterion=section_data['criterion'],
                        score=section_data.get('score'),
                        comments=section_data.get('comments'),
                    )
        
        response_serializer = EvaluationSerializer(evaluation)
        return Response(response_serializer.data)
    
    def destroy(self, request, pk=None):
        """Delete evaluation and its sections."""
        evaluation = self.get_object()
        evaluation.delete()
        return Response({'success': True, 'message': 'Evaluation deleted successfully'})
    
    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        """Validate or invalidate evaluation."""
        evaluation = self.get_object()
        serializer = ValidateEvaluationRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        validated = serializer.validated_data.get('validated', True)
        
        if validated:
            evaluation.validated = True
            evaluation.validated_at = timezone.now()
        else:
            evaluation.validated = False
            evaluation.validated_at = None
        
        evaluation.save()
        
        response_serializer = EvaluationSerializer(evaluation)
        return Response(response_serializer.data)
    
    @action(detail=True, methods=['get', 'post'], url_path='sections')
    def sections(self, request, pk=None):
        """Get or add evaluation sections."""
        evaluation = self.get_object()
        
        if request.method == 'GET':
            # List sections
            sections = EvaluationSection.objects.filter(evaluation=evaluation).order_by('id')
            serializer = EvaluationSectionSerializer(sections, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            # Add new section
            serializer = CreateEvaluationSectionRequest(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            section = EvaluationSection.objects.create(
                evaluation=evaluation,
                criterion=serializer.validated_data['criterion'],
                score=serializer.validated_data.get('score'),
                comments=serializer.validated_data.get('comments'),
            )
            
            response_serializer = EvaluationSectionSerializer(section)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
