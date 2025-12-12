"""
Serializers for COMM-SERVICE models
"""
from rest_framework import serializers
from .models import Message, Notification, Document, EmailQueue
from .service_client import AuthServiceClient, ProfileServiceClient, CoreServiceClient


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for Message (includes sender/receiver user data)"""
    sender_data = serializers.SerializerMethodField()
    receiver_data = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id', 'sender_id', 'receiver_id', 'subject', 'body',
            'created_at', 'read_at', 'metadata',
            'sender_data', 'receiver_data'
        ]
        read_only_fields = ['id', 'created_at']

    def get_sender_data(self, obj):
        """Fetch sender user data from AUTH-SERVICE"""
        return AuthServiceClient.get_user_by_id(str(obj.sender_id))

    def get_receiver_data(self, obj):
        """Fetch receiver user data from AUTH-SERVICE"""
        return AuthServiceClient.get_user_by_id(str(obj.receiver_id))


class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating messages (without user_data)"""

    class Meta:
        model = Message
        fields = [
            'sender_id', 'receiver_id', 'subject', 'body', 'metadata'
        ]


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification (includes user data)"""
    user_data = serializers.SerializerMethodField()
    related_object_data = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id', 'user_id', 'type', 'title', 'content',
            'related_object_type', 'related_object_id',
            'created_at', 'sent_at', 'status', 'attempts', 'last_error',
            'metadata', 'user_data', 'related_object_data'
        ]
        read_only_fields = ['id', 'created_at', 'sent_at', 'attempts', 'last_error']

    def get_user_data(self, obj):
        """Fetch user data from AUTH-SERVICE"""
        return AuthServiceClient.get_user_by_id(str(obj.user_id))

    def get_related_object_data(self, obj):
        """
        Fetch related object data based on related_object_type
        Returns None if no related object
        """
        if not obj.related_object_type or not obj.related_object_id:
            return None

        related_type = obj.related_object_type.lower()
        related_id = str(obj.related_object_id)

        if related_type == 'offer':
            return CoreServiceClient.get_offer_by_id(related_id)
        elif related_type == 'stage':
            return CoreServiceClient.get_stage_by_id(related_id)
        elif related_type == 'student':
            return ProfileServiceClient.get_student_by_id(related_id)
        elif related_type == 'encadrant':
            return ProfileServiceClient.get_encadrant_by_id(related_id)
        else:
            return None


class NotificationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating notifications (without enriched data)"""

    class Meta:
        model = Notification
        fields = [
            'user_id', 'type', 'title', 'content',
            'related_object_type', 'related_object_id', 'metadata'
        ]


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document (includes owner/student data)"""
    owner_data = serializers.SerializerMethodField()
    student_data = serializers.SerializerMethodField()
    offer_data = serializers.SerializerMethodField()
    uploaded_by_data = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            'id', 'owner_user_id', 'student_id', 'offer_id',
            'storage_path', 'filename', 'content_type', 'size_bytes',
            'uploaded_by', 'uploaded_at', 'metadata',
            'owner_data', 'student_data', 'offer_data', 'uploaded_by_data'
        ]
        read_only_fields = ['id', 'uploaded_at']

    def get_owner_data(self, obj):
        """Fetch owner user data from AUTH-SERVICE"""
        if obj.owner_user_id:
            return AuthServiceClient.get_user_by_id(str(obj.owner_user_id))
        return None

    def get_student_data(self, obj):
        """Fetch student data from PROFILE-SERVICE"""
        if obj.student_id:
            return ProfileServiceClient.get_student_by_id(str(obj.student_id))
        return None

    def get_offer_data(self, obj):
        """Fetch offer data from CORE-SERVICE"""
        if obj.offer_id:
            return CoreServiceClient.get_offer_by_id(str(obj.offer_id))
        return None

    def get_uploaded_by_data(self, obj):
        """Fetch uploader user data from AUTH-SERVICE"""
        if obj.uploaded_by:
            return AuthServiceClient.get_user_by_id(str(obj.uploaded_by))
        return None


class DocumentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating documents (without enriched data)"""

    class Meta:
        model = Document
        fields = [
            'owner_user_id', 'student_id', 'offer_id',
            'storage_path', 'filename', 'content_type', 'size_bytes',
            'uploaded_by', 'metadata'
        ]


class EmailQueueSerializer(serializers.ModelSerializer):
    """Serializer for EmailQueue"""

    class Meta:
        model = EmailQueue
        fields = [
            'id', 'to_addresses', 'subject', 'body', 'headers',
            'created_at', 'scheduled_at', 'sent_at',
            'status', 'attempts', 'last_error'
        ]
        read_only_fields = ['id', 'created_at', 'sent_at', 'attempts', 'last_error']


class EmailQueueCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating email queue entries"""

    class Meta:
        model = EmailQueue
        fields = [
            'to_addresses', 'subject', 'body', 'headers', 'scheduled_at'
        ]
