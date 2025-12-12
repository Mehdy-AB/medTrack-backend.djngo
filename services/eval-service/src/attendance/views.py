"""Views for attendance app."""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from .models import AttendanceRecord, AttendanceSummary
from .serializers import (
    AttendanceRecordSerializer,
    AttendanceRecordWithDetailsSerializer,
    MarkAttendanceRequest,
    UpdateAttendanceRequest,
    BulkMarkAttendanceRequest,
    AttendanceSummarySerializer,
    AttendanceSummaryWithDetailsSerializer
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


class AttendanceViewSet(viewsets.ModelViewSet):
    """ViewSet for attendance records."""
    queryset = AttendanceRecord.objects.all()
    serializer_class = AttendanceRecordSerializer
    
    def get_serializer_class(self):
        """Use detailed serializer for list/retrieve."""
        if self.action in ['list', 'retrieve']:
            return AttendanceRecordWithDetailsSerializer
        return AttendanceRecordSerializer
    
    def get_queryset(self):
        """Filter attendance records based on query parameters."""
        queryset = AttendanceRecord.objects.all()
        
        # Required filter: offer_id
        offer_id = self.request.query_params.get('offer_id')
        if offer_id:
            queryset = queryset.filter(offer_id=offer_id)
        
        # Optional filters
        student_id = self.request.query_params.get('student_id')
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        
        # Date filtering
        date = self.request.query_params.get('date')
        if date:
            queryset = queryset.filter(date=date)
        
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            queryset = queryset.filter(date__range=[start_date, end_date])
        elif start_date:
            queryset = queryset.filter(date__gte=start_date)
        elif end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        # Boolean filters
        is_present = self.request.query_params.get('is_present')
        if is_present is not None:
            queryset = queryset.filter(is_present=is_present.lower() == 'true')
        
        justified = self.request.query_params.get('justified')
        if justified is not None:
            queryset = queryset.filter(justified=justified.lower() == 'true')
        
        return queryset.order_by('-date', 'student_id')
    
    def create(self, request):
        """Mark attendance for a student."""
        serializer = MarkAttendanceRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_id = get_user_id_from_request(request)
        
        # Create or update attendance record
        attendance, created = AttendanceRecord.objects.update_or_create(
            student_id=serializer.validated_data['student_id'],
            offer_id=serializer.validated_data['offer_id'],
            date=serializer.validated_data['date'],
            defaults={
                'is_present': serializer.validated_data['is_present'],
                'justified': serializer.validated_data.get('justified', False),
                'justification_reason': serializer.validated_data.get('justification_reason'),
                'marked_by': user_id,
            }
        )
        
        # Update attendance summary
        self._update_attendance_summary(
            serializer.validated_data['student_id'],
            serializer.validated_data['offer_id']
        )
        
        response_serializer = AttendanceRecordSerializer(attendance)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
    
    def update(self, request, pk=None):
        """Update attendance record."""
        attendance = self.get_object()
        serializer = UpdateAttendanceRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Update fields
        for field, value in serializer.validated_data.items():
            setattr(attendance, field, value)
        attendance.save()
        
        # Update summary
        self._update_attendance_summary(attendance.student_id, attendance.offer_id)
        
        response_serializer = AttendanceRecordSerializer(attendance)
        return Response(response_serializer.data)
    
    def destroy(self, request, pk=None):
        """Delete attendance record."""
        attendance = self.get_object()
        student_id = attendance.student_id
        offer_id = attendance.offer_id
        
        attendance.delete()
        
        # Update summary
        self._update_attendance_summary(student_id, offer_id)
        
        return Response({'success': True, 'message': 'Attendance record deleted'})
    
    @action(detail=False, methods=['post'], url_path='bulk')
    def bulk_mark(self, request):
        """Bulk mark attendance for multiple students."""
        serializer = BulkMarkAttendanceRequest(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_id = get_user_id_from_request(request)
        offer_id = serializer.validated_data['offer_id']
        date = serializer.validated_data['date']
        records = serializer.validated_data['records']
        
        created_records = []
        for record_data in records:
            attendance, _ = AttendanceRecord.objects.update_or_create(
                student_id=record_data['student_id'],
                offer_id=offer_id,
                date=date,
                defaults={
                    'is_present': record_data['is_present'],
                    'justified': record_data.get('justified', False),
                    'justification_reason': record_data.get('justification_reason'),
                    'marked_by': user_id,
                }
            )
            created_records.append(attendance)
            
            # Update summary for each student
            self._update_attendance_summary(record_data['student_id'], offer_id)
        
        response_serializer = AttendanceRecordSerializer(created_records, many=True)
        return Response(response_serializer.data)
    
    def _update_attendance_summary(self, student_id, offer_id):
        """Update or create attendance summary for a student."""
        # Get all attendance records for this student/offer
        records = AttendanceRecord.objects.filter(
            student_id=student_id,
            offer_id=offer_id
        )
        
        total_days = records.count()
        present_days = records.filter(is_present=True).count()
        
        # Calculate presence rate
        presence_rate = (present_days / total_days * 100) if total_days > 0 else 0
        
        # Update or create summary
        summary, _ = AttendanceSummary.objects.update_or_create(
            student_id=student_id,
            offer_id=offer_id,
            defaults={
                'total_days': total_days,
                'present_days': present_days,
                'presence_rate': round(presence_rate, 2),
            }
        )
        
        return summary


class AttendanceSummaryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for attendance summaries."""
    queryset = AttendanceSummary.objects.all()
    serializer_class = AttendanceSummarySerializer
    
    def get_serializer_class(self):
        """Use detailed serializer for list/retrieve."""
        if self.action in ['list', 'retrieve']:
            return AttendanceSummaryWithDetailsSerializer
        return AttendanceSummarySerializer
    
    def get_queryset(self):
        """Filter summaries based on query parameters."""
        queryset = AttendanceSummary.objects.all()
        
        # Filters
        student_id = self.request.query_params.get('student_id')
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        
        offer_id = self.request.query_params.get('offer_id')
        if offer_id:
            queryset = queryset.filter(offer_id=offer_id)
        
        validated = self.request.query_params.get('validated')
        if validated is not None:
            queryset = queryset.filter(validated=validated.lower() == 'true')
        
        min_presence_rate = self.request.query_params.get('min_presence_rate')
        if min_presence_rate:
            queryset = queryset.filter(presence_rate__gte=float(min_presence_rate))
        
        return queryset.order_by('-presence_rate')
    
    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        """Validate attendance summary (>=80% check)."""
        summary = self.get_object()
        
        validated = request.data.get('validated', True)
        
        if validated:
            summary.validated = True
            summary.validated_at = timezone.now()
        else:
            summary.validated = False
            summary.validated_at = None
        
        summary.save()
        
        serializer = AttendanceSummarySerializer(summary)
        return Response(serializer.data)
