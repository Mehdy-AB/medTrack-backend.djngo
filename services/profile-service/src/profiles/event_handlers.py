"""
Event handlers for PROFILE-SERVICE
Consumes events from other services (mainly AUTH-SERVICE) and creates profiles automatically
"""
import logging
from .models import Student, Encadrant, Establishment, Service
from .events import EventTypes, publish_event

logger = logging.getLogger(__name__)


# ============================================
# USER EVENTS (from AUTH-SERVICE)
# ============================================

def handle_user_created(event: dict):
    """
    Handle user.created event from AUTH-SERVICE or external service

    When a user is created by your friend's service or AUTH-SERVICE,
    automatically create the appropriate profile based on role.

    Event payload:
    {
        "user_id": "uuid",
        "email": "user@example.com",
        "role": "student" or "encadrant" or "admin",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+1234567890",
        "cin": "AB123456" (optional, for students)
    }
    """
    payload = event['payload']
    user_id = payload['user_id']
    email = payload['email']
    role = payload.get('role', 'student')
    first_name = payload.get('first_name', '')
    last_name = payload.get('last_name', '')
    phone = payload.get('phone', '')
    cin = payload.get('cin')

    logger.info(f"👤 Processing user.created for {email} with role: {role}")

    try:
        if role == 'student':
            # Check if student already exists
            if Student.objects.filter(user_id=user_id).exists():
                logger.warning(f"⚠️  Student with user_id {user_id} already exists, skipping creation")
                return

            # Create student profile
            student = Student.objects.create(
                user_id=user_id,
                cin=cin or f"AUTO-{user_id[:8]}",  # Auto-generate CIN if not provided
                email=email,
                phone=phone,
                first_name=first_name,
                last_name=last_name,
                metadata={
                    'created_from_event': True,
                    'source_service': event.get('service', 'unknown')
                }
            )

            logger.info(f"✅ Created student profile: {student.id} for user {user_id}")

            # Publish student.created event
            publish_event(
                event_type=EventTypes.STUDENT_CREATED,
                payload={
                    'student_id': str(student.id),
                    'user_id': str(student.user_id),
                    'cin': student.cin,
                    'email': student.email,
                    'phone': student.phone,
                    'first_name': student.first_name,
                    'last_name': student.last_name
                },
                service_name='profile-service'
            )

            logger.info(f"📤 Published student.created event for {student.id}")

        elif role == 'encadrant':
            # Check if encadrant already exists
            if Encadrant.objects.filter(user_id=user_id).exists():
                logger.warning(f"⚠️  Encadrant with user_id {user_id} already exists, skipping creation")
                return

            # Create encadrant profile
            encadrant = Encadrant.objects.create(
                user_id=user_id,
                email=email,
                phone=phone,
                first_name=first_name,
                last_name=last_name,
                metadata={
                    'created_from_event': True,
                    'source_service': event.get('service', 'unknown')
                }
            )

            logger.info(f"✅ Created encadrant profile: {encadrant.id} for user {user_id}")

            # Publish encadrant.created event
            publish_event(
                event_type=EventTypes.ENCADRANT_CREATED,
                payload={
                    'encadrant_id': str(encadrant.id),
                    'user_id': str(encadrant.user_id),
                    'email': encadrant.email,
                    'phone': encadrant.phone,
                    'first_name': encadrant.first_name,
                    'last_name': encadrant.last_name
                },
                service_name='profile-service'
            )

            logger.info(f"📤 Published encadrant.created event for {encadrant.id}")

        else:
            logger.info(f"ℹ️  User role '{role}' does not require profile creation")

    except Exception as e:
        logger.error(f"❌ Error creating profile for user {user_id}: {e}", exc_info=True)
        raise  # Re-raise to trigger message requeue


def handle_user_deleted(event: dict):
    """
    Handle user.deleted event

    When a user is deleted, delete their associated profiles
    """
    payload = event['payload']
    user_id = payload['user_id']

    logger.info(f"🗑️  Processing user.deleted for user {user_id}")

    try:
        # Delete student if exists
        students = Student.objects.filter(user_id=user_id)
        if students.exists():
            for student in students:
                student_id = str(student.id)
                student.delete()
                logger.info(f"✅ Deleted student {student_id}")

                # Publish student.deleted event
                publish_event(
                    event_type=EventTypes.STUDENT_DELETED,
                    payload={
                        'student_id': student_id,
                        'user_id': user_id
                    },
                    service_name='profile-service'
                )

        # Delete encadrant if exists
        encadrants = Encadrant.objects.filter(user_id=user_id)
        if encadrants.exists():
            for encadrant in encadrants:
                encadrant_id = str(encadrant.id)
                encadrant.delete()
                logger.info(f"✅ Deleted encadrant {encadrant_id}")

                # Publish encadrant.deleted event
                publish_event(
                    event_type=EventTypes.ENCADRANT_DELETED,
                    payload={
                        'encadrant_id': encadrant_id,
                        'user_id': user_id
                    },
                    service_name='profile-service'
                )

    except Exception as e:
        logger.error(f"❌ Error deleting profiles for user {user_id}: {e}", exc_info=True)
        raise


# ============================================
# EVENT ROUTER
# ============================================

EVENT_HANDLERS = {
    EventTypes.USER_CREATED: handle_user_created,
    EventTypes.USER_DELETED: handle_user_deleted,
}


def route_event(event: dict):
    """
    Route incoming event to appropriate handler

    Args:
        event: Event dictionary with structure:
            {
                "event_type": "user.created",
                "payload": {...},
                "service": "auth-service",
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
