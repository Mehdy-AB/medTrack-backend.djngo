"""
Pydantic schemas for Django Ninja API
"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


# ============================================
# MESSAGE SCHEMAS
# ============================================

class MessageCreate(BaseModel):
    """Schema for creating a new message"""
    sender_id: UUID
    receiver_id: UUID
    subject: Optional[str] = None
    body: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class MessageResponse(BaseModel):
    """Schema for message response (with enriched data)"""
    id: UUID
    sender_id: UUID
    receiver_id: UUID
    subject: Optional[str]
    body: Optional[str]
    created_at: datetime
    read_at: Optional[datetime]
    metadata: Dict[str, Any]
    sender_data: Optional[Dict[str, Any]] = None
    receiver_data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# ============================================
# NOTIFICATION SCHEMAS
# ============================================

class NotificationCreate(BaseModel):
    """Schema for creating a notification"""
    user_id: UUID
    type: str = Field(..., pattern='^(email|push|system)$')
    title: Optional[str] = None
    content: Optional[str] = None
    related_object_type: Optional[str] = None
    related_object_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class NotificationResponse(BaseModel):
    """Schema for notification response"""
    id: UUID
    user_id: UUID
    type: str
    title: Optional[str]
    content: Optional[str]
    related_object_type: Optional[str]
    related_object_id: Optional[UUID]
    created_at: datetime
    sent_at: Optional[datetime]
    status: str
    attempts: int
    last_error: Optional[str]
    metadata: Dict[str, Any]
    user_data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# ============================================
# DOCUMENT SCHEMAS
# ============================================

class DocumentUploadResponse(BaseModel):
    """Schema for document upload response"""
    id: UUID
    storage_path: str
    filename: Optional[str]
    content_type: Optional[str]
    size_bytes: Optional[int]
    uploaded_at: datetime
    download_url: Optional[str] = None
    expires_in: int = 3600  # URL expiration in seconds


class DocumentResponse(BaseModel):
    """Schema for document response (with enriched data)"""
    id: UUID
    owner_user_id: Optional[UUID]
    student_id: Optional[UUID]
    offer_id: Optional[UUID]
    storage_path: str
    filename: Optional[str]
    content_type: Optional[str]
    size_bytes: Optional[int]
    uploaded_by: Optional[UUID]
    uploaded_at: datetime
    metadata: Dict[str, Any]
    download_url: Optional[str] = None
    owner_data: Optional[Dict[str, Any]] = None
    student_data: Optional[Dict[str, Any]] = None
    offer_data: Optional[Dict[str, Any]] = None
    uploaded_by_data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# ============================================
# EMAIL QUEUE SCHEMAS
# ============================================

class EmailQueueCreate(BaseModel):
    """Schema for creating email queue entry"""
    recipient_email: str
    subject: Optional[str] = None
    body: Optional[str] = None
    related_user_id: Optional[UUID] = None
    related_notification_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class EmailQueueResponse(BaseModel):
    """Schema for email queue response"""
    id: UUID
    recipient_email: str
    subject: Optional[str]
    body: Optional[str]
    status: str
    attempts: int
    last_attempt_at: Optional[datetime]
    sent_at: Optional[datetime]
    error_message: Optional[str]
    related_user_id: Optional[UUID]
    related_notification_id: Optional[UUID]
    created_at: datetime
    metadata: Dict[str, Any]
    user_data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
