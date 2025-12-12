# MedTrack Event-Driven Architecture

## Overview

This document explains the complete event-driven communication system using RabbitMQ for the MedTrack microservices platform.

---

## Architecture Principles

### ✅ Rules
1. **HTTP GET only** for reading data from other services
2. **RabbitMQ events** for all actions/state changes
3. **No HTTP POST** between services
4. **Automatic retry** - RabbitMQ stores events if service is down
5. **Decoupled services** - services don't need to know about each other

### Event Flow Example

```
Frontend → POST /profile/api/students/
    ↓
PROFILE-SERVICE creates student in database
    ↓
PROFILE-SERVICE publishes event: "student.created"
    ↓
RabbitMQ Exchange → Routes to queues
    ↓
Multiple services consume the event:
    - AUTH-SERVICE: Creates user account
    - COMM-SERVICE: Sends welcome notification
    - CORE-SERVICE: Initializes student stage tracking
```

---

## RabbitMQ Configuration

### Exchange & Queue Structure

```
Exchange: medtrack.events (topic)
    ↓
Queues:
    - auth.events (consumes: user.*, student.*, encadrant.*)
    - profile.events (consumes: user.created, auth.verified)
    - comm.events (consumes: student.*, stage.*, notification.*)
    - core.events (consumes: student.*, encadrant.*)
    - eval.events (consumes: stage.*, student.*)
```

---

## Event Types

### AUTH-SERVICE Events

| Event Name | Payload | Published When |
|------------|---------|----------------|
| `user.created` | `{user_id, email, role, first_name, last_name}` | User registered |
| `user.verified` | `{user_id, email}` | Email verified |
| `user.password_changed` | `{user_id}` | Password updated |
| `user.deleted` | `{user_id}` | User account deleted |

### PROFILE-SERVICE Events

| Event Name | Payload | Published When |
|------------|---------|----------------|
| `student.created` | `{student_id, user_id, cin, email, phone}` | Student profile created |
| `student.updated` | `{student_id, updated_fields}` | Student profile updated |
| `student.deleted` | `{student_id, user_id}` | Student deleted |
| `encadrant.created` | `{encadrant_id, user_id, email, phone}` | Encadrant created |
| `encadrant.updated` | `{encadrant_id, updated_fields}` | Encadrant updated |
| `establishment.created` | `{establishment_id, name, city}` | Establishment added |

### CORE-SERVICE Events

| Event Name | Payload | Published When |
|------------|---------|----------------|
| `offer.created` | `{offer_id, title, establishment_id}` | Internship offer posted |
| `offer.updated` | `{offer_id, status, updated_fields}` | Offer modified |
| `stage.created` | `{stage_id, student_id, offer_id, start_date}` | Stage assigned |
| `stage.accepted` | `{stage_id, student_id, encadrant_id}` | Stage accepted |
| `stage.started` | `{stage_id, actual_start_date}` | Stage began |
| `stage.completed` | `{stage_id, completion_date}` | Stage finished |
| `stage.cancelled` | `{stage_id, reason}` | Stage cancelled |

### COMM-SERVICE Events

| Event Name | Payload | Published When |
|------------|---------|----------------|
| `message.sent` | `{message_id, sender_id, receiver_id, subject}` | Message sent |
| `notification.created` | `{notification_id, user_id, type, title}` | Notification created |
| `document.uploaded` | `{document_id, student_id, filename, size}` | File uploaded |
| `email.sent` | `{email_id, recipient, subject}` | Email sent successfully |
| `email.failed` | `{email_id, recipient, error}` | Email send failed |

### EVAL-SERVICE Events

| Event Name | Payload | Published When |
|------------|---------|----------------|
| `evaluation.created` | `{evaluation_id, stage_id, student_id, score}` | Evaluation submitted |
| `evaluation.updated` | `{evaluation_id, new_score}` | Evaluation modified |
| `grade.assigned` | `{student_id, stage_id, final_grade}` | Final grade assigned |

---

## Implementation

### 1. Shared Event Library

Create a common library for all services:

**File**: `/shared/events.py`

```python
"""
Shared event definitions and RabbitMQ utilities
Copy this file to each microservice
"""
import json
import logging
import pika
from typing import Dict, Any, Callable
from datetime import datetime

logger = logging.getLogger(__name__)

# Event type definitions
class EventTypes:
    # AUTH events
    USER_CREATED = "user.created"
    USER_VERIFIED = "user.verified"
    USER_PASSWORD_CHANGED = "user.password_changed"
    USER_DELETED = "user.deleted"

    # PROFILE events
    STUDENT_CREATED = "student.created"
    STUDENT_UPDATED = "student.updated"
    STUDENT_DELETED = "student.deleted"
    ENCADRANT_CREATED = "encadrant.created"
    ENCADRANT_UPDATED = "encadrant.updated"
    ESTABLISHMENT_CREATED = "establishment.created"

    # CORE events
    OFFER_CREATED = "offer.created"
    OFFER_UPDATED = "offer.updated"
    STAGE_CREATED = "stage.created"
    STAGE_ACCEPTED = "stage.accepted"
    STAGE_STARTED = "stage.started"
    STAGE_COMPLETED = "stage.completed"
    STAGE_CANCELLED = "stage.cancelled"

    # COMM events
    MESSAGE_SENT = "message.sent"
    NOTIFICATION_CREATED = "notification.created"
    DOCUMENT_UPLOADED = "document.uploaded"
    EMAIL_SENT = "email.sent"
    EMAIL_FAILED = "email.failed"

    # EVAL events
    EVALUATION_CREATED = "evaluation.created"
    EVALUATION_UPDATED = "evaluation.updated"
    GRADE_ASSIGNED = "grade.assigned"


class RabbitMQClient:
    """RabbitMQ client for publishing and consuming events"""

    EXCHANGE_NAME = "medtrack.events"
    EXCHANGE_TYPE = "topic"

    def __init__(self, host: str, port: int, user: str, password: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.connection = None
        self.channel = None

    def connect(self):
        """Establish connection to RabbitMQ"""
        credentials = pika.PlainCredentials(self.user, self.password)
        parameters = pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()

        # Declare exchange
        self.channel.exchange_declare(
            exchange=self.EXCHANGE_NAME,
            exchange_type=self.EXCHANGE_TYPE,
            durable=True
        )
        logger.info(f"Connected to RabbitMQ at {self.host}:{self.port}")

    def publish_event(self, event_type: str, payload: Dict[str, Any], service_name: str):
        """
        Publish an event to RabbitMQ

        Args:
            event_type: Event type (e.g., "student.created")
            payload: Event data
            service_name: Name of publishing service
        """
        if not self.channel:
            self.connect()

        event = {
            "event_type": event_type,
            "payload": payload,
            "service": service_name,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0"
        }

        message = json.dumps(event)

        self.channel.basic_publish(
            exchange=self.EXCHANGE_NAME,
            routing_key=event_type,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
                content_type="application/json"
            )
        )

        logger.info(f"Published event: {event_type} from {service_name}")

    def declare_queue(self, queue_name: str, routing_keys: list):
        """
        Declare a queue and bind it to routing keys

        Args:
            queue_name: Name of the queue
            routing_keys: List of routing keys to bind (e.g., ["student.*", "user.created"])
        """
        if not self.channel:
            self.connect()

        # Declare queue
        self.channel.queue_declare(queue=queue_name, durable=True)

        # Bind queue to exchange with routing keys
        for routing_key in routing_keys:
            self.channel.queue_bind(
                exchange=self.EXCHANGE_NAME,
                queue=queue_name,
                routing_key=routing_key
            )

        logger.info(f"Queue {queue_name} declared with bindings: {routing_keys}")

    def consume_events(self, queue_name: str, callback: Callable):
        """
        Start consuming events from a queue

        Args:
            queue_name: Name of the queue to consume from
            callback: Function to call for each message
        """
        if not self.channel:
            self.connect()

        def on_message(ch, method, properties, body):
            try:
                event = json.loads(body)
                logger.info(f"Received event: {event['event_type']}")

                # Call the callback
                callback(event)

                # Acknowledge message
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logger.error(f"Error processing event: {e}")
                # Reject and requeue message
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=on_message
        )

        logger.info(f"Starting to consume from queue: {queue_name}")
        self.channel.start_consuming()

    def close(self):
        """Close connection"""
        if self.connection:
            self.connection.close()
            logger.info("RabbitMQ connection closed")


# Singleton instance
_rabbitmq_client = None

def get_rabbitmq_client(host: str, port: int, user: str, password: str) -> RabbitMQClient:
    """Get or create RabbitMQ client singleton"""
    global _rabbitmq_client
    if _rabbitmq_client is None:
        _rabbitmq_client = RabbitMQClient(host, port, user, password)
    return _rabbitmq_client
```

---

## Usage Examples

### Example 1: PROFILE-SERVICE publishes "student.created"

**When**: Student is created via `POST /profile/api/students/`

```python
# profile-service/src/profiles/views.py

from .events import get_rabbitmq_client, EventTypes
import os

def create_student(request):
    # Create student in database
    student = Student.objects.create(
        user_id=request.data['user_id'],
        cin=request.data['cin'],
        email=request.data['email'],
        # ... other fields
    )

    # Publish event
    rabbitmq = get_rabbitmq_client(
        host=os.environ.get('RABBITMQ_HOST', 'rabbitmq'),
        port=5672,
        user=os.environ.get('RABBITMQ_USER', 'admin'),
        password=os.environ.get('RABBITMQ_PASSWORD', 'password')
    )

    rabbitmq.publish_event(
        event_type=EventTypes.STUDENT_CREATED,
        payload={
            "student_id": str(student.id),
            "user_id": str(student.user_id),
            "cin": student.cin,
            "email": student.email,
            "phone": student.phone,
            "first_name": student.first_name,
            "last_name": student.last_name
        },
        service_name="profile-service"
    )

    return Response(StudentSerializer(student).data, status=201)
```

### Example 2: COMM-SERVICE consumes "student.created"

**Action**: Send welcome notification to new student

```python
# comm-service/src/communications/event_handlers.py

from .models import Notification
from .events import EventTypes
import logging

logger = logging.getLogger(__name__)

def handle_student_created(event: dict):
    """
    Handle student.created event
    Send welcome notification to new student
    """
    payload = event['payload']
    student_id = payload['student_id']
    user_id = payload['user_id']
    first_name = payload.get('first_name', 'Student')

    # Create welcome notification
    notification = Notification.objects.create(
        user_id=user_id,
        type='system',
        title='Welcome to MedTrack!',
        content=f'Hello {first_name}! Your student profile has been created successfully.',
        metadata={'student_id': student_id}
    )

    logger.info(f"Created welcome notification for student {student_id}")

    # Could also trigger WebSocket broadcast here
    # broadcast_notification(user_id, notification)


def handle_stage_accepted(event: dict):
    """
    Handle stage.accepted event
    Send notification to student
    """
    payload = event['payload']
    student_id = payload['student_id']
    stage_id = payload['stage_id']

    # Get student's user_id (via HTTP GET - allowed!)
    # student = get_student_by_id(student_id)

    notification = Notification.objects.create(
        user_id=payload.get('user_id'),  # Ideally included in event
        type='system',
        title='Stage Accepted!',
        content=f'Your internship stage has been accepted and will begin soon.',
        related_object_type='stage',
        related_object_id=stage_id,
        metadata={'stage_id': stage_id, 'student_id': student_id}
    )

    logger.info(f"Created stage acceptance notification for student {student_id}")


# Event handler registry
EVENT_HANDLERS = {
    EventTypes.STUDENT_CREATED: handle_student_created,
    EventTypes.STAGE_ACCEPTED: handle_stage_accepted,
    EventTypes.STAGE_COMPLETED: lambda e: logger.info(f"Stage completed: {e['payload']}"),
    # Add more handlers...
}


def route_event(event: dict):
    """Route event to appropriate handler"""
    event_type = event['event_type']
    handler = EVENT_HANDLERS.get(event_type)

    if handler:
        try:
            handler(event)
        except Exception as e:
            logger.error(f"Error handling event {event_type}: {e}")
    else:
        logger.warning(f"No handler for event type: {event_type}")
```

### Example 3: Consumer Service (Django Management Command)

**File**: `comm-service/src/communications/management/commands/consume_events.py`

```python
from django.core.management.base import BaseCommand
from communications.events import get_rabbitmq_client
from communications.event_handlers import route_event
import os

class Command(BaseCommand):
    help = 'Consume RabbitMQ events for COMM-SERVICE'

    def handle(self, *args, **options):
        rabbitmq = get_rabbitmq_client(
            host=os.environ.get('RABBITMQ_HOST', 'rabbitmq'),
            port=5672,
            user=os.environ.get('RABBITMQ_USER', 'admin'),
            password=os.environ.get('RABBITMQ_PASSWORD', 'password')
        )

        # Declare queue and bindings
        rabbitmq.declare_queue(
            queue_name='comm.events',
            routing_keys=[
                'student.*',      # All student events
                'stage.*',        # All stage events
                'user.created',   # Specific user event
                'encadrant.*'     # All encadrant events
            ]
        )

        self.stdout.write(self.style.SUCCESS('Starting event consumer...'))

        # Start consuming
        rabbitmq.consume_events(
            queue_name='comm.events',
            callback=route_event
        )
```

**Run consumer**:
```bash
docker exec -it comm-service python manage.py consume_events
```

---

## Docker Configuration

### Update Dockerfile to run event consumer

**File**: `services/comm-service/Dockerfile`

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ .
COPY register_service.py .
COPY consul/ ./consul/

EXPOSE 8000

# Run migrations, register service, start web server AND event consumer in background
CMD python manage.py migrate --noinput && \
    python register_service.py && \
    python manage.py consume_events & \
    daphne -b 0.0.0.0 -p 8000 comm_service.asgi:application
```

---

## External Service Integration (For Your Friend)

### API for External Services

**Endpoint**: `POST /events/webhook`

Allow external services to publish events via HTTP (converts to RabbitMQ internally)

```python
# shared-gateway/src/events/views.py

from ninja import NinjaAPI, Schema
from .rabbitmq_client import get_rabbitmq_client

api = NinjaAPI()

class EventPublishRequest(Schema):
    event_type: str
    payload: dict
    service_name: str = "external-service"

@api.post("/events/publish")
def publish_event(request, event: EventPublishRequest):
    """
    Allow external services to publish events

    Example:
    POST /events/publish
    {
        "event_type": "student.created",
        "payload": {
            "student_id": "uuid",
            "user_id": "uuid",
            "email": "student@example.com"
        },
        "service_name": "external-registration-system"
    }
    """
    rabbitmq = get_rabbitmq_client()

    rabbitmq.publish_event(
        event_type=event.event_type,
        payload=event.payload,
        service_name=event.service_name
    )

    return {"success": True, "message": f"Event {event.event_type} published"}
```

### For Your Friend's Microservice

**Python Example**:

```python
import requests

# Publish student.created event
response = requests.post(
    'http://medtrack-api.com/events/publish',
    json={
        "event_type": "student.created",
        "payload": {
            "student_id": "550e8400-e29b-41d4-a716-446655440000",
            "user_id": "660e9500-f39c-52e5-b827-557766551111",
            "cin": "AB123456",
            "email": "student@example.com",
            "phone": "+1234567890",
            "first_name": "John",
            "last_name": "Doe"
        },
        "service_name": "external-registration-service"
    },
    headers={'Authorization': 'Bearer API_KEY'}
)
```

**Node.js Example**:

```javascript
const axios = require('axios');

async function publishStudentCreated(student) {
    const response = await axios.post('http://medtrack-api.com/events/publish', {
        event_type: 'student.created',
        payload: {
            student_id: student.id,
            user_id: student.userId,
            cin: student.cin,
            email: student.email,
            phone: student.phone,
            first_name: student.firstName,
            last_name: student.lastName
        },
        service_name: 'external-registration-service'
    }, {
        headers: { 'Authorization': 'Bearer API_KEY' }
    });

    return response.data;
}
```

---

## Testing Events

### Publish Test Event

```bash
# Using curl
curl -X POST http://localhost/events/publish \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "student.created",
    "payload": {
      "student_id": "550e8400-e29b-41d4-a716-446655440000",
      "user_id": "660e9500-f39c-52e5-b827-557766551111",
      "email": "test@example.com"
    },
    "service_name": "test-service"
  }'
```

### Monitor RabbitMQ

1. **Web UI**: http://localhost:15672
   - Username: `admin`
   - Password: `password`

2. **Check queues**: See how many messages are queued
3. **Check consumers**: See which services are consuming
4. **View messages**: Inspect event payloads

---

## Complete Event Flow Example

### Scenario: Student Registration Complete Workflow

```
1. Frontend → POST /auth/api/register
   AUTH-SERVICE creates user
   → Publishes: user.created

2. PROFILE-SERVICE consumes user.created
   → Creates student profile
   → Publishes: student.created

3. COMM-SERVICE consumes student.created
   → Sends welcome notification
   → Publishes: notification.created

4. AUTH-SERVICE consumes student.created
   → Sends verification email
   → Publishes: email.sent

5. CORE-SERVICE consumes student.created
   → Initializes stage tracking
   → Publishes: stage.tracking_initialized
```

All services work independently. If COMM-SERVICE is down, RabbitMQ stores the events until it comes back online!

---

## Benefits

✅ **Resilient**: Services can be down, events are queued
✅ **Decoupled**: Services don't need to know about each other
✅ **Scalable**: Easy to add new consumers
✅ **Auditable**: All events are logged
✅ **Flexible**: New services can consume existing events
✅ **No cascading failures**: One service failure doesn't break others

---

## Next Steps

1. Copy `events.py` to each microservice
2. Add event publishers to create/update/delete operations
3. Add event handlers for consumed events
4. Add event consumer management commands
5. Update Dockerfiles to run consumers
6. Test event flow end-to-end
