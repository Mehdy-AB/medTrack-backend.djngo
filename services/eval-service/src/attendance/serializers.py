"""Serializers for attendance app."""
from rest_framework import serializers
from django.utils import timezone
from .models import AttendanceRecord, AttendanceSummary
from utils.service_client import get_profile_client


class MarkAttendanceRequest(serializers.Serializer):
    """Request serializer for marking attendance."""
    student_id = serializers.UUIDField()
    offer_id = serializers.UUIDField()
    date = serializers.DateField()
    is_present = serializers.BooleanField()
    justified = serializers.BooleanField(default=False)
    justification_reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class UpdateAttendanceRequest(serializers.Serializer):
    """Request serializer for updating attendance."""
    is_present = serializers.BooleanField(required=False)
    justified = serializers.BooleanField(required=False)
    justification_reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class AttendanceRecordSerializer(serializers.ModelSerializer):
    """Basic serializer for attendance records."""
    
    class Meta:
        model = AttendanceRecord
        fields = [
            'id', 'student_id', 'offer_id', 'date', 'is_present',
            'justified', 'justification_reason', 'marked_by', 'marked_at'
        ]
        read_only_fields = ['id', 'marked_at']


class AttendanceRecordWithDetailsSerializer(serializers.ModelSerializer):
    """Attendance record with nested student details from PROFILE-SERVICE."""
    student = serializers.SerializerMethodField()
    
    class Meta:
        model = AttendanceRecord
        fields = [
            'id', 'student_id', 'offer_id', 'date', 'is_present',
            'justified', 'justification_reason', 'marked_by', 'marked_at',
            'student'
        ]
        read_only_fields = ['id', 'marked_at']
    
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


class BulkAttendanceRecordRequest(serializers.Serializer):
    """Single record in bulk attendance request."""
    student_id = serializers.UUIDField()
    is_present = serializers.BooleanField()
    justified = serializers.BooleanField(default=False)
    justification_reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class BulkMarkAttendanceRequest(serializers.Serializer):
    """Request serializer for bulk marking attendance."""
    offer_id = serializers.UUIDField()
    date = serializers.DateField()
    records = BulkAttendanceRecordRequest(many=True)
    
    def validate_records(self, value):
        """Ensure records list is not empty."""
        if not value:
            raise serializers.ValidationError("Records list cannot be empty")
        return value


class AttendanceSummarySerializer(serializers.ModelSerializer):
    """Basic serializer for attendance summaries."""
    
    class Meta:
        model = AttendanceSummary
        fields = [
            'id', 'student_id', 'offer_id', 'total_days', 'present_days',
            'presence_rate', 'validated', 'validated_at'
        ]
        read_only_fields = ['id', 'presence_rate']


class AttendanceSummaryWithDetailsSerializer(serializers.ModelSerializer):
    """Attendance summary with nested student and offer details."""
    student = serializers.SerializerMethodField()
    offer = serializers.SerializerMethodField()
    
    class Meta:
        model = AttendanceSummary
        fields = [
            'id', 'student_id', 'offer_id', 'total_days', 'present_days',
            'presence_rate', 'validated', 'validated_at',
            'student', 'offer'
        ]
        read_only_fields = ['id', 'presence_rate']
    
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
        """Fetch offer details from CORE-SERVICE via Consul."""
        try:
            # You can implement this when CORE-SERVICE is accessible
            # For now, return None or basic info
            return {
                'title': None,
                'period_start': None,
                'period_end': None,
            }
        except Exception as e:
            print(f"Error fetching offer details: {e}")
        return None
