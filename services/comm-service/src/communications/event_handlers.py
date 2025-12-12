"""
Event handlers for COMM-SERVICE
Handles events from other microservices and triggers appropriate actions
"""
import logging
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Notification, Message
from .events import EventTypes
from .service_client import AuthServiceClient, ProfileServiceClient

logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()


# ============================================
# STUDENT EVENTS
# ============================================

def handle_student_created(event: dict):
    """
    Handle student.created event from PROFILE-SERVICE

    Action: Send welcome notification to new student

    Event payload:
    {
        "student_id": "uuid",
        "user_id": "uuid",
        "cin": "AB123456",
        "email": "student@example.com",
        "phone": "+1234567890",
        "first_name": "John",
        "last_name": "Doe"
    }
    """
    payload = event['payload']
    student_id = payload['student_id']
    user_id = payload['user_id']
    first_name = payload.get('first_name', 'Student')
    last_name = payload.get('last_name', '')

    # Create welcome notification
    notification = Notification.objects.create(
        user_id=user_id,
        type='system',
        title='Welcome to MedTrack!',
        content=f'Hello {first_name} {last_name}! Your student profile has been created successfully. '
                f'You can now browse internship offers and apply for stages.',
        related_object_type='student',
        related_object_id=student_id,
        metadata={
            'student_id': student_id,
            'event': 'student.created'
        }
    )

    logger.info(f"✅ Created welcome notification for student {student_id}")

    # Broadcast via WebSocket
    try:
        async_to_sync(channel_layer.group_send)(
            f'user_{user_id}',
            {
                'type': 'notification_created',
                'data': {
                    'id': str(notification.id),
                    'title': notification.title,
                    'content': notification.content,
                    'type': notification.type
                }
            }
        )
        logger.info(f"📡 WebSocket broadcast sent for student {student_id}")
    except Exception as e:
        logger.error(f"❌ Failed to broadcast notification: {e}")


def handle_student_updated(event: dict):
    """
    Handle student.updated event

    Action: Log the update (could send notification if needed)
    """
    payload = event['payload']
    student_id = payload['student_id']
    updated_fields = payload.get('updated_fields', [])

    logger.info(f"📝 Student {student_id} updated fields: {updated_fields}")


def handle_student_deleted(event: dict):
    """
    Handle student.deleted event

    Action: Clean up student-related notifications/documents
    """
    payload = event['payload']
    student_id = payload['student_id']
    user_id = payload['user_id']

    # Could delete student-related data here
    # For now, just log
    logger.info(f"🗑️ Student {student_id} deleted")


# ============================================
# ENCADRANT EVENTS
# ============================================

def handle_encadrant_created(event: dict):
    """
    Handle encadrant.created event from PROFILE-SERVICE

    Action: Send welcome notification to new encadrant
    """
    payload = event['payload']
    encadrant_id = payload['encadrant_id']
    user_id = payload['user_id']
    first_name = payload.get('first_name', 'Encadrant')
    last_name = payload.get('last_name', '')

    notification = Notification.objects.create(
        user_id=user_id,
        type='system',
        title='Welcome as Encadrant!',
        content=f'Hello Dr. {last_name}! Your encadrant profile has been created. '
                f'You can now supervise students during their internships.',
        related_object_type='encadrant',
        related_object_id=encadrant_id,
        metadata={
            'encadrant_id': encadrant_id,
            'event': 'encadrant.created'
        }
    )

    logger.info(f"✅ Created welcome notification for encadrant {encadrant_id}")

    # Broadcast via WebSocket
    try:
        async_to_sync(channel_layer.group_send)(
            f'user_{user_id}',
            {
                'type': 'notification_created',
                'data': {
                    'id': str(notification.id),
                    'title': notification.title,
                    'content': notification.content
                }
            }
        )
    except Exception as e:
        logger.error(f"❌ Failed to broadcast: {e}")


# ============================================
# STAGE EVENTS
# ============================================

def handle_stage_created(event: dict):
    """
    Handle stage.created event from CORE-SERVICE

    Action: Notify student that stage assignment is pending
    """
    payload = event['payload']
    stage_id = payload['stage_id']
    student_id = payload['student_id']
    offer_id = payload.get('offer_id')

    # Get student data to find user_id
    student = ProfileServiceClient.get_student_by_id(student_id)
    if not student:
        logger.warning(f"⚠️  Student {student_id} not found for stage notification")
        return

    user_id = student.get('user_id')

    notification = Notification.objects.create(
        user_id=user_id,
        type='system',
        title='New Stage Assignment',
        content=f'A new internship stage has been created for you. Waiting for acceptance.',
        related_object_type='stage',
        related_object_id=stage_id,
        metadata={
            'stage_id': stage_id,
            'student_id': student_id,
            'offer_id': offer_id,
            'event': 'stage.created'
        }
    )

    logger.info(f"✅ Created stage assignment notification for student {student_id}")

    # WebSocket broadcast
    try:
        async_to_sync(channel_layer.group_send)(
            f'user_{user_id}',
            {
                'type': 'notification_created',
                'data': {
                    'id': str(notification.id),
                    'title': notification.title,
                    'content': notification.content
                }
            }
        )
    except Exception as e:
        logger.error(f"❌ WebSocket broadcast failed: {e}")


def handle_stage_accepted(event: dict):
    """
    Handle stage.accepted event

    Action: Send congratulations notification to student
    """
    payload = event['payload']
    stage_id = payload['stage_id']
    student_id = payload['student_id']
    encadrant_id = payload.get('encadrant_id')
    start_date = payload.get('start_date')

    # Get student user_id
    student = ProfileServiceClient.get_student_by_id(student_id)
    if not student:
        return

    user_id = student.get('user_id')

    notification = Notification.objects.create(
        user_id=user_id,
        type='system',
        title='🎉 Stage Accepted!',
        content=f'Congratulations! Your internship stage has been accepted and will begin on {start_date}.',
        related_object_type='stage',
        related_object_id=stage_id,
        metadata={
            'stage_id': stage_id,
            'student_id': student_id,
            'encadrant_id': encadrant_id,
            'event': 'stage.accepted'
        }
    )

    logger.info(f"✅ Stage acceptance notification sent to student {student_id}")

    # WebSocket
    try:
        async_to_sync(channel_layer.group_send)(
            f'user_{user_id}',
            {
                'type': 'notification_created',
                'data': {
                    'id': str(notification.id),
                    'title': notification.title,
                    'content': notification.content
                }
            }
        )
    except Exception as e:
        logger.error(f"❌ Broadcast failed: {e}")


def handle_stage_started(event: dict):
    """Handle stage.started event"""
    payload = event['payload']
    stage_id = payload['stage_id']
    actual_start_date = payload.get('actual_start_date')

    logger.info(f"🏁 Stage {stage_id} started on {actual_start_date}")


def handle_stage_completed(event: dict):
    """
    Handle stage.completed event

    Action: Send completion notification
    """
    payload = event['payload']
    stage_id = payload['stage_id']
    student_id = payload.get('student_id')
    completion_date = payload.get('completion_date')

    # Get student
    student = ProfileServiceClient.get_student_by_id(student_id)
    if not student:
        return

    user_id = student.get('user_id')

    notification = Notification.objects.create(
        user_id=user_id,
        type='system',
        title='✅ Stage Completed!',
        content=f'Your internship stage has been marked as completed on {completion_date}. '
                f'Please wait for your evaluation.',
        related_object_type='stage',
        related_object_id=stage_id,
        metadata={
            'stage_id': stage_id,
            'completion_date': completion_date,
            'event': 'stage.completed'
        }
    )

    logger.info(f"✅ Stage completion notification sent to student {student_id}")


def handle_stage_cancelled(event: dict):
    """Handle stage.cancelled event"""
    payload = event['payload']
    stage_id = payload['stage_id']
    reason = payload.get('reason', 'No reason provided')

    logger.warning(f"⚠️  Stage {stage_id} cancelled: {reason}")


# ============================================
# EVALUATION EVENTS
# ============================================

def handle_evaluation_created(event: dict):
    """
    Handle evaluation.created event from EVAL-SERVICE

    Action: Notify student that they've been evaluated
    """
    payload = event['payload']
    evaluation_id = payload['evaluation_id']
    stage_id = payload['stage_id']
    student_id = payload['student_id']
    score = payload.get('score')

    # Get student
    student = ProfileServiceClient.get_student_by_id(student_id)
    if not student:
        return

    user_id = student.get('user_id')

    notification = Notification.objects.create(
        user_id=user_id,
        type='system',
        title='📊 New Evaluation',
        content=f'Your internship has been evaluated. Score: {score}/100',
        related_object_type='evaluation',
        related_object_id=evaluation_id,
        metadata={
            'evaluation_id': evaluation_id,
            'stage_id': stage_id,
            'score': score,
            'event': 'evaluation.created'
        }
    )

    logger.info(f"✅ Evaluation notification sent to student {student_id}")

    # WebSocket
    try:
        async_to_sync(channel_layer.group_send)(
            f'user_{user_id}',
            {
                'type': 'notification_created',
                'data': {
                    'id': str(notification.id),
                    'title': notification.title,
                    'content': notification.content
                }
            }
        )
    except Exception as e:
        logger.error(f"❌ Broadcast failed: {e}")


def handle_grade_assigned(event: dict):
    """Handle grade.assigned event"""
    payload = event['payload']
    student_id = payload['student_id']
    stage_id = payload['stage_id']
    final_grade = payload['final_grade']

    logger.info(f"🎓 Grade assigned to student {student_id}: {final_grade}")


# ============================================
# USER EVENTS
# ============================================

def handle_user_created(event: dict):
    """Handle user.created event from AUTH-SERVICE"""
    payload = event['payload']
    user_id = payload['user_id']
    email = payload['email']
    role = payload.get('role', 'user')

    logger.info(f"👤 New user created: {email} ({role})")


# ============================================
# OFFER EVENTS
# ============================================

def handle_offer_created(event: dict):
    """
    Handle offer.created event from CORE-SERVICE

    Action: Could notify relevant students about new offer
    """
    payload = event['payload']
    offer_id = payload['offer_id']
    title = payload.get('title', 'New Internship Offer')

    logger.info(f"💼 New offer created: {title} ({offer_id})")
    # Could send notifications to students here


# ============================================
# EVENT ROUTER
# ============================================

EVENT_HANDLERS = {
    # Student events
    EventTypes.STUDENT_CREATED: handle_student_created,
    EventTypes.STUDENT_UPDATED: handle_student_updated,
    EventTypes.STUDENT_DELETED: handle_student_deleted,

    # Encadrant events
    EventTypes.ENCADRANT_CREATED: handle_encadrant_created,

    # Stage events
    EventTypes.STAGE_CREATED: handle_stage_created,
    EventTypes.STAGE_ACCEPTED: handle_stage_accepted,
    EventTypes.STAGE_STARTED: handle_stage_started,
    EventTypes.STAGE_COMPLETED: handle_stage_completed,
    EventTypes.STAGE_CANCELLED: handle_stage_cancelled,

    # Evaluation events
    EventTypes.EVALUATION_CREATED: handle_evaluation_created,
    EventTypes.GRADE_ASSIGNED: handle_grade_assigned,

    # User events
    EventTypes.USER_CREATED: handle_user_created,

    # Offer events
    EventTypes.OFFER_CREATED: handle_offer_created,
}


def route_event(event: dict):
    """
    Route incoming event to appropriate handler

    Args:
        event: Event dictionary with structure:
            {
                "event_type": "student.created",
                "payload": {...},
                "service": "profile-service",
                "timestamp": "2025-01-15T10:00:00Z",
                "version": "1.0"
            }
    """
    event_type = event.get('event_type')
    service = event.get('service', 'unknown')

    logger.info(f"🔀 Routing event: {event_type} from {service}")

    handler = EVENT_HANDLERS.get(event_type)

    if handler:
        try:
            handler(event)
            logger.info(f"✅ Successfully handled event: {event_type}")
        except Exception as e:
            logger.error(f"❌ Error handling event {event_type}: {e}", exc_info=True)
            raise  # Re-raise to trigger message requeue
    else:
        logger.warning(f"⚠️  No handler registered for event type: {event_type}")
