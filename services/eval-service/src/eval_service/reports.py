"""Views for statistics and reports."""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Q, Avg
from datetime import datetime
from attendance.models import AttendanceRecord, AttendanceSummary
from evaluations.models import Evaluation, EvaluationSection
from utils.service_client import get_profile_client, get_core_client


class AttendanceStatisticsView(APIView):
    """Get attendance statistics for an offer."""
    
    def get(self, request):
        """Calculate attendance statistics."""
        offer_id = request.query_params.get('offer_id')
        if not offer_id:
            return Response(
                {'error': 'offer_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Optional date filters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Base queryset
        queryset = AttendanceRecord.objects.filter(offer_id=offer_id)
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        # Overall statistics
        total_records = queryset.count()
        present_records = queryset.filter(is_present=True).count()
        absence_records = total_records - present_records
        justified_absences = queryset.filter(is_present=False, justified=True).count()
        
        # Calculate presence rate
        presence_rate = (present_records / total_records * 100) if total_records > 0 else 0
        
        # Group by student
        student_stats = {}
        student_records = queryset.values('student_id').annotate(
            total=Count('id'),
            present=Count('id', filter=Q(is_present=True))
        )
        
        by_student = []
        profile_client = get_profile_client()
        
        for student_record in student_records:
            student_id = str(student_record['student_id'])
            total = student_record['total']
            present = student_record['present']
            student_presence_rate = (present / total * 100) if total > 0 else 0
            
            # Fetch student name
            student_name = 'Unknown'
            try:
                student = profile_client.get_student_details(student_id)
                if student:
                    first_name = student.get('first_name', '')
                    last_name = student.get('last_name', '')
                    student_name = f"{first_name} {last_name}".strip() or student.get('student_number', 'Unknown')
            except Exception as e:
                print(f"Error fetching student {student_id}: {e}")
            
            by_student.append({
                'student_id': student_id,
                'student_name': student_name,
                'presence_rate': round(student_presence_rate, 2),
                'total_days': total,
                'present_days': present,
            })
        
        # Sort by presence rate descending
        by_student.sort(key=lambda x: x['presence_rate'], reverse=True)
        
        return Response({
            'total_days': total_records,
            'present_days': present_records,
            'absence_days': absence_records,
            'justified_absences': justified_absences,
            'presence_rate': round(presence_rate, 2),
            'by_student': by_student,
        })


class EvaluationReportView(APIView):
    """Generate evaluation report for a student."""
    
    def get(self, request, student_id):
        """Get comprehensive evaluation report."""
        offer_id = request.query_params.get('offer_id')
        report_format = request.query_params.get('format', 'json')
        
        # Base queryset
        evaluations_qs = Evaluation.objects.filter(student_id=student_id)
        if offer_id:
            evaluations_qs = evaluations_qs.filter(offer_id=offer_id)
        
        # Get student details
        student_info = None
        try:
            profile_client = get_profile_client()
            student = profile_client.get_student_details(student_id)
            if student:
                student_info = {
                    'id': student_id,
                    'first_name': student.get('first_name'),
                    'last_name': student.get('last_name'),
                    'student_number': student.get('student_number'),
                }
        except Exception as e:
            print(f"Error fetching student: {e}")
        
        # Get attendance summary
        attendance_summaries = AttendanceSummary.objects.filter(student_id=student_id)
        if offer_id:
            attendance_summaries = attendance_summaries.filter(offer_id=offer_id)
        
        attendance_data = []
        for summary in attendance_summaries:
            attendance_data.append({
                'offer_id': str(summary.offer_id),
                'total_days': summary.total_days,
                'present_days': summary.present_days,
                'presence_rate': float(summary.presence_rate),
                'validated': summary.validated,
            })
        
        # Get evaluations
        evaluations_data = []
        core_client = get_core_client()
        
        for evaluation in evaluations_qs:
            # Get offer details
            offer_title = None
            try:
                offer = core_client.get_offer_details(str(evaluation.offer_id))
                if offer:
                    offer_title = offer.get('title')
            except Exception as e:
                print(f"Error fetching offer: {e}")
            
            # Get sections
            sections = EvaluationSection.objects.filter(evaluation=evaluation)
            sections_data = [{
                'criterion': section.criterion,
                'score': float(section.score) if section.score else None,
                'comments': section.comments,
            } for section in sections]
            
            evaluations_data.append({
                'id': str(evaluation.id),
                'offer_id': str(evaluation.offer_id),
                'offer_title': offer_title,
                'grade': float(evaluation.grade) if evaluation.grade else None,
                'comments': evaluation.comments,
                'submitted_at': evaluation.submitted_at.isoformat(),
                'validated': evaluation.validated,
                'sections': sections_data,
            })
        
        # Calculate overall statistics
        total_evaluations = len(evaluations_data)
        validated_evaluations = len([e for e in evaluations_data if e['validated']])
        
        grades = [e['grade'] for e in evaluations_data if e['grade'] is not None]
        average_grade = sum(grades) / len(grades) if grades else None
        
        overall_attendance_rate = None
        if attendance_data:
            total_days = sum(a['total_days'] for a in attendance_data)
            total_present = sum(a['present_days'] for a in attendance_data)
            overall_attendance_rate = (total_present / total_days * 100) if total_days > 0 else 0
        
        report = {
            'student': student_info,
            'summary': {
                'total_evaluations': total_evaluations,
                'validated_evaluations': validated_evaluations,
                'average_grade': round(average_grade, 2) if average_grade else None,
                'overall_attendance_rate': round(overall_attendance_rate, 2) if overall_attendance_rate else None,
            },
            'attendance': attendance_data,
            'evaluations': evaluations_data,
            'generated_at': datetime.now().isoformat(),
        }
        
        if report_format == 'json':
            return Response(report)
        elif report_format == 'pdf':
            # For now, return JSON with a note (PDF generation would require additional libraries)
            return Response({
                'message': 'PDF generation not yet implemented',
                'data': report
            }, status=status.HTTP_501_NOT_IMPLEMENTED)
        else:
            return Response(
                {'error': 'Invalid format. Use json or pdf'},
                status=status.HTTP_400_BAD_REQUEST
            )
