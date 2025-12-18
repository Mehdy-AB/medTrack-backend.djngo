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
            'id', 'code', 'name', 'type', 'address', 'city', 'wilaya', 'email', 'phone',
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
    user_id = serializers.UUIDField(read_only=True)
    user_data = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            'id', 'user_id', 'cin', 'email', 'phone', 'first_name', 'last_name',
            'student_number', 'date_of_birth', 'university', 'program', 'year_level',
            'metadata', 'user_data', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user_id', 'created_at', 'updated_at']

    def get_user_data(self, obj):
        """Fetch user data from AUTH-SERVICE"""
        return AuthServiceClient.get_user_by_id(str(obj.user_id))


class StudentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating students (without user_data)"""

    password = serializers.CharField(write_only=True, required=False, min_length=6)
    user_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Student
        fields = [
            'id', 'user_id', 'cin', 'email', 'phone', 'first_name', 'last_name',
            'student_number', 'date_of_birth', 'university', 'program', 
            'year_level', 'metadata', 'password'
        ]
        read_only_fields = ['id', 'user_id']
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'cin': {'required': False},
            'phone': {'required': False},
            'student_number': {'required': False},
            'date_of_birth': {'required': False},
            'university': {'required': False},
            'program': {'required': False},
            'year_level': {'required': False},
            'metadata': {'required': False},
        }


class EncadrantSerializer(serializers.ModelSerializer):
    """Serializer for Encadrant (supervisors/mentors)"""
    user_data = serializers.SerializerMethodField()
    establishment_name = serializers.CharField(source='establishment.name', read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)

    class Meta:
        model = Encadrant
        fields = [
            'id', 'user_id', 'cin', 'email', 'phone', 'first_name', 'last_name',
            'establishment', 'establishment_name', 'service', 'service_name', 
            'position', 'speciality', 'metadata', 'user_data', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_user_data(self, obj):
        """Fetch user data from AUTH-SERVICE"""
        return AuthServiceClient.get_user_by_id(str(obj.user_id))


class EncadrantCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating encadrants (without user_data)"""

    password = serializers.CharField(write_only=True, required=False, min_length=6)

    class Meta:
        model = Encadrant
        fields = [
            'id', 'user_id', 'cin', 'email', 'phone', 'first_name', 'last_name',
            'establishment', 'service', 'position', 'speciality', 'metadata', 'password'
        ]
        read_only_fields = ['id', 'user_id']
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'cin': {'required': False},
            'phone': {'required': False},
            'establishment': {'required': False},
            'service': {'required': False},
            'position': {'required': False},
            'speciality': {'required': False},
            'metadata': {'required': False},
        }
