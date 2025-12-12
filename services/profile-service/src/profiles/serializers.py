"""
Serializers for PROFILE-SERVICE models
"""
from rest_framework import serializers
from .models import Establishment, Service, Student, Encadrant
from .service_client import AuthServiceClient


class EstablishmentSerializer(serializers.ModelSerializer):
    """Serializer for Establishment (hospitals)"""

    class Meta:
        model = Establishment
        fields = [
            'id', 'name', 'type', 'address', 'city', 'phone',
            'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ServiceSerializer(serializers.ModelSerializer):
    """Serializer for Service (hospital departments)"""
    establishment_name = serializers.CharField(source='establishment.name', read_only=True)

    class Meta:
        model = Service
        fields = [
            'id', 'establishment', 'establishment_name', 'name',
            'description', 'capacity', 'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StudentSerializer(serializers.ModelSerializer):
    """Serializer for Student profiles"""
    user_data = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            'id', 'user_id', 'student_number', 'date_of_birth',
            'university', 'program', 'year_level', 'extra',
            'user_data', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_user_data(self, obj):
        """Fetch user data from AUTH-SERVICE"""
        return AuthServiceClient.get_user_by_id(str(obj.user_id))


class StudentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating students (without user_data)"""

    class Meta:
        model = Student
        fields = [
            'user_id', 'student_number', 'date_of_birth',
            'university', 'program', 'year_level', 'extra'
        ]


class EncadrantSerializer(serializers.ModelSerializer):
    """Serializer for Encadrant (supervisors/mentors)"""
    user_data = serializers.SerializerMethodField()
    establishment_name = serializers.CharField(source='establishment.name', read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)

    class Meta:
        model = Encadrant
        fields = [
            'id', 'user_id', 'establishment', 'establishment_name',
            'service', 'service_name', 'position', 'specialty',
            'contact', 'user_data', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_user_data(self, obj):
        """Fetch user data from AUTH-SERVICE"""
        return AuthServiceClient.get_user_by_id(str(obj.user_id))


class EncadrantCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating encadrants (without user_data)"""

    class Meta:
        model = Encadrant
        fields = [
            'user_id', 'establishment', 'service',
            'position', 'specialty', 'contact'
        ]