# MedTrack Event-Driven Microservices Architecture

## Overview

This project implements a complete event-driven microservices architecture using **RabbitMQ** for asynchronous communication between services. All services communicate via events - **no HTTP POST between services**.

---

## Architecture Principles

### Communication Rules

✅ **HTTP GET** - For reading data between services (e.g., getting user info)
✅ **RabbitMQ Events** - For all actions and state changes
❌ **HTTP POST** - NOT used between services

### Benefits

- **Decoupled**: Services don't need to know each other's APIs
- **Resilient**: Events are queued if a service is down
- **Scalable**: Easy to add new event consumers
- **Real-time**: WebSocket notifications for users
- **External Integration**: External services can publish events

---

## Services Overview

### 1. PROFILE-SERVICE ✅

**Responsibilities:**
- Manages student and encadrant profiles
- Auto-creates profiles when receiving `user.created` events
- Manages establishments and services (hospitals/departments)

**Consumes Events:**
- `user.created` → Creates Student or Encadrant profile based on role
- `user.deleted` → Deletes associated profiles

**Publishes Events:**
- `student.created`, `student.updated`, `student.deleted`
- `encadrant.created`, `encadrant.updated`, `encadrant.deleted`
- `establishment.created`, `establishment.updated`
- `service.created`, `service.updated`

**Event Consumer:**
```bash
docker exec -it profile-service bash
cd /app/src
python manage.py consume_events
```

**Files:**
- `services/profile-service/src/profiles/events.py` - RabbitMQ client
- `services/profile-service/src/profiles/event_handlers.py` - Event handlers
- `services/profile-service/src/profiles/views.py` - ViewSets with event publishing
- `services/profile-service/src/profiles/management/commands/consume_events.py`

### 2. COMM-SERVICE ✅

**Responsibilities:**
- Sends notifications to users
- Manages messages between users
- Handles document storage (MinIO)
- Email queue management
- Real-time WebSocket broadcasting

**Consumes Events:**
- `student.created` → Sends welcome notification
- `encadrant.created` → Sends welcome notification
- `stage.created` → Notifies student of assignment
- `stage.accepted` → Sends "🎉 Stage Accepted!" notification
- `stage.completed` → Sends completion notification
- `evaluation.created` → Notifies student of score

**Publishes Events:**
- `message.sent`, `message.read`
- `notification.created`
- `document.uploaded`, `document.deleted`

**Event Consumer:**
```bash
docker exec -it comm-service bash
cd /app/src
python manage.py consume_events
```

**Files:**
- `services/comm-service/src/communications/events.py` - RabbitMQ client
- `services/comm-service/src/communications/event_handlers.py` - Event handlers
- `services/comm-service/src/communications/api.py` - Django Ninja API with events
- `services/comm-service/src/communications/management/commands/consume_events.py`

### 3. AUTH-SERVICE 🔧

**Responsibilities:**
- User authentication and authorization
- User management
- JWT token generation/validation

**Should Publish Events:**
- `user.created` - When user registers or is created
- `user.verified` - When email verified
- `user.deleted` - When user deleted
- `user.password_changed` - When password changed

**Implementation Status:**
- ✅ RabbitMQ client ready (`events.py` copied)
- ✅ Dependency added (`pika==1.3.2`)
- ⏭️ Need to implement User models/views to publish events

**Files:**
- `services/auth-service/src/auth_service/events.py` - RabbitMQ client (ready)
- `services/auth-service/requirements.txt` - pika dependency added

### 4. CORE-SERVICE 🔧

**Responsibilities:**
- Manages internship offers
- Manages stage assignments (internships)
- Student applications for offers

**Should Publish Events:**
- `offer.created`, `offer.updated`, `offer.deleted`
- `stage.created`, `stage.accepted`, `stage.rejected`
- `stage.started`, `stage.completed`, `stage.cancelled`
- `application.submitted`, `application.approved`, `application.rejected`

**Implementation Status:**
- ✅ RabbitMQ client ready (`events.py` copied)
- ✅ Dependency added (`pika==1.3.2`)
- ⏭️ Need to implement Offer/Stage models/views to publish events

**Files:**
- `services/core-service/src/core_service/events.py` - RabbitMQ client (ready)
- `services/core-service/requirements.txt` - pika dependency added

### 5. EVAL-SERVICE ⏭️

**Responsibilities:**
- Student evaluations
- Grade management
- Attendance tracking

**Should Publish Events:**
- `evaluation.created`, `evaluation.updated`, `evaluation.deleted`
- `grade.assigned`, `grade.updated`
- `attendance.marked`

**Implementation Status:**
- ⏭️ Not yet started

---

## Event Types Reference

### User Events (AUTH-SERVICE)
- `user.created` - User registered/created
- `user.verified` - Email verified
- `user.deleted` - User deleted
- `user.password_changed` - Password changed

### Profile Events (PROFILE-SERVICE)
- `student.created` - Student profile created
- `student.updated` - Student profile updated
- `student.deleted` - Student profile deleted
- `encadrant.created` - Encadrant profile created
- `encadrant.updated` - Encadrant profile updated
- `encadrant.deleted` - Encadrant profile deleted
- `establishment.created` - Hospital created
- `establishment.updated` - Hospital updated
- `service.created` - Department created
- `service.updated` - Department updated

### Offer/Stage Events (CORE-SERVICE)
- `offer.created` - Internship offer posted
- `offer.updated` - Offer updated
- `offer.deleted` - Offer removed
- `stage.created` - Stage assignment created
- `stage.accepted` - Stage accepted by student/admin
- `stage.rejected` - Stage rejected
- `stage.started` - Stage begins (actual start date)
- `stage.completed` - Stage finished
- `stage.cancelled` - Stage cancelled

### Communication Events (COMM-SERVICE)
- `message.sent` - Message sent between users
- `message.read` - Message marked as read
- `notification.created` - Notification created
- `document.uploaded` - Document uploaded
- `document.deleted` - Document deleted

### Evaluation Events (EVAL-SERVICE)
- `evaluation.created` - Evaluation created by encadrant
- `evaluation.updated` - Evaluation updated
- `grade.assigned` - Final grade assigned
- `attendance.marked` - Attendance recorded

---

## Complete Event Flow Example

### User Registration → Profile Creation → Welcome Notification

```
1. External service or AUTH-SERVICE
   ↓ Publishes event to RabbitMQ
   {
     "event_type": "user.created",
     "payload": {
       "user_id": "uuid",
       "email": "student@example.com",
       "role": "student",  ← Determines profile type
       "first_name": "John",
       "last_name": "Doe"
     },
     "service": "auth-service",
     "timestamp": "2025-01-15T10:00:00Z"
   }

2. RabbitMQ
   ↓ Routes to queue: profile.events
   ↓ Based on routing key: user.created

3. PROFILE-SERVICE Consumer
   ↓ Consumes event from profile.events
   ↓ handle_user_created() function
   ↓ Checks role field
   ↓ Creates Student in database
   ↓ Publishes event to RabbitMQ
   {
     "event_type": "student.created",
     "payload": {
       "student_id": "uuid",
       "user_id": "uuid",
       "email": "student@example.com",
       "first_name": "John",
       "last_name": "Doe"
     },
     "service": "profile-service"
   }

4. RabbitMQ
   ↓ Routes to queue: comm.events
   ↓ Based on routing key: student.created

5. COMM-SERVICE Consumer
   ↓ Consumes event from comm.events
   ↓ handle_student_created() function
   ↓ Creates Notification in database
   ↓ Broadcasts via WebSocket
   {
     "type": "notification_created",
     "data": {
       "title": "Welcome to MedTrack!",
       "content": "Hello John! Your student profile has been created..."
     }
   }

6. User receives real-time notification!
```

### Stage Acceptance → Congratulations Notification

```
1. CORE-SERVICE API Call
   POST /core/api/stages/{id}/accept/
   ↓ Stage status updated to "accepted"
   ↓ Publishes event to RabbitMQ
   {
     "event_type": "stage.accepted",
     "payload": {
       "stage_id": "uuid",
       "student_id": "uuid",
       "encadrant_id": "uuid",
       "start_date": "2025-02-15"
     },
     "service": "core-service"
   }

2. RabbitMQ
   ↓ Routes to queue: comm.events

3. COMM-SERVICE Consumer
   ↓ handle_stage_accepted() function
   ↓ Gets student user_id from PROFILE-SERVICE (HTTP GET)
   ↓ Creates Notification
   ↓ Broadcasts via WebSocket
   {
     "title": "🎉 Stage Accepted!",
     "content": "Congratulations! Your internship has been accepted..."
   }

4. Student receives notification!
```

---

## RabbitMQ Configuration

### Exchange
- **Name**: `medtrack.events`
- **Type**: `topic`
- **Durable**: Yes

### Queues

| Queue Name | Service | Routing Keys |
|------------|---------|--------------|
| `profile.events` | PROFILE-SERVICE | `user.created`, `user.deleted` |
| `comm.events` | COMM-SERVICE | `student.*`, `encadrant.*`, `stage.*`, `evaluation.*`, `offer.created`, `grade.*` |
| `core.events` | CORE-SERVICE | `student.*`, `evaluation.created`, `grade.assigned` |
| `eval.events` | EVAL-SERVICE | `stage.completed`, `student.created` |

### Routing Key Pattern

Format: `{entity}.{action}`

Examples:
- `user.created`
- `student.updated`
- `stage.accepted`
- `evaluation.created`

Wildcards:
- `student.*` - All student events
- `*.created` - All creation events

---

## How to Publish Events from Controllers

### Example: User Registration in AUTH-SERVICE

```python
from auth_service.events import publish_event, EventTypes

def register_user(email, password, role, first_name, last_name):
    # 1. Create user in database
    user = User.objects.create(
        email=email,
        role=role,
        first_name=first_name,
        last_name=last_name
    )
    user.set_password(password)
    user.save()

    # 2. Publish event to RabbitMQ
    try:
        publish_event(
            event_type=EventTypes.USER_CREATED,
            payload={
                'user_id': str(user.id),
                'email': user.email,
                'role': user.role,  # Important: student or encadrant
                'first_name': user.first_name,
                'last_name': user.last_name,
                'created_at': user.created_at.isoformat()
            },
            service_name='auth-service'
        )
        logger.info(f"📤 Published user.created for {user.email}")
    except Exception as e:
        logger.error(f"Failed to publish event: {e}")

    return user
```

### Example: Stage Acceptance in CORE-SERVICE

```python
from core_service.events import publish_event, EventTypes
from django.utils import timezone

def accept_stage(stage_id):
    # 1. Update stage status
    stage = Stage.objects.get(id=stage_id)
    stage.status = 'accepted'
    stage.save()

    # 2. Publish event to RabbitMQ
    try:
        publish_event(
            event_type=EventTypes.STAGE_ACCEPTED,
            payload={
                'stage_id': str(stage.id),
                'student_id': str(stage.student_id),
                'encadrant_id': str(stage.encadrant_id),
                'start_date': stage.start_date.isoformat(),
                'accepted_at': timezone.now().isoformat()
            },
            service_name='core-service'
        )
        logger.info(f"📤 Published stage.accepted for stage {stage.id}")
    except Exception as e:
        logger.error(f"Failed to publish event: {e}")

    return stage
```

---

## Running Event Consumers

Event consumers must run alongside the web servers.

### Development Mode (Separate Terminals)

```bash
# Terminal 1: PROFILE-SERVICE consumer
docker exec -it profile-service bash
cd /app/src
python manage.py consume_events

# Terminal 2: COMM-SERVICE consumer
docker exec -it comm-service bash
cd /app/src
python manage.py consume_events
```

### Production Mode (Docker Compose)

Update service commands to run both web server and consumer:

```yaml
# Example for profile-service
profile-service:
  command: >
    sh -c "
      python manage.py migrate --noinput &&
      python register_service.py &&
      python manage.py consume_events &
      gunicorn profiles.wsgi:application --bind 0.0.0.0:8000 --workers 2
    "
```

Or use separate containers:

```yaml
profile-service:
  # Web server

profile-consumer:
  build: ./services/profile-service
  command: python manage.py consume_events
  depends_on:
    - rabbitmq
    - postgres
```

---

## Testing Event Flow

### 1. Start All Consumers

```bash
# PROFILE-SERVICE
docker exec -it profile-service bash -c "cd /app/src && python manage.py consume_events" &

# COMM-SERVICE
docker exec -it comm-service bash -c "cd /app/src && python manage.py consume_events" &
```

### 2. Publish a Test Event

**From RabbitMQ Container:**

```bash
docker exec -it rabbitmq bash

# Install Python
apt-get update && apt-get install -y python3 python3-pip
pip3 install pika

# Create test script
cat > /tmp/test_user_event.py << 'EOF'
import pika
import json
from datetime import datetime
import uuid

connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host='localhost',
        credentials=pika.PlainCredentials('admin', 'password')
    )
)
channel = connection.channel()

event = {
    "event_type": "user.created",
    "payload": {
        "user_id": str(uuid.uuid4()),
        "email": "test@example.com",
        "role": "student",
        "first_name": "Test",
        "last_name": "User"
    },
    "service": "test-service",
    "timestamp": datetime.utcnow().isoformat(),
    "version": "1.0"
}

channel.basic_publish(
    exchange='medtrack.events',
    routing_key='user.created',
    body=json.dumps(event),
    properties=pika.BasicProperties(delivery_mode=2)
)

print("✅ Published test event")
connection.close()
EOF

python3 /tmp/test_user_event.py
```

### 3. Verify Results

**Check Consumer Logs:**
```bash
docker logs profile-service -f | grep -E "📤|📨"
docker logs comm-service -f | grep -E "📤|📨"
```

**Check Database:**
```bash
# Check student created
docker exec -it postgres psql -U postgres -d profile_db -c \
  "SELECT id, user_id, email, first_name FROM profiles_student ORDER BY created_at DESC LIMIT 5;"

# Check notification created
docker exec -it postgres psql -U postgres -d comm_db -c \
  "SELECT id, type, title FROM communications_notification ORDER BY created_at DESC LIMIT 5;"
```

---

## Monitoring

### RabbitMQ Management UI

**URL**: http://localhost:15672
**Credentials**: admin / password

**What to Monitor:**
- Queue depths (should be low if consumers running)
- Message rates (publish/deliver)
- Consumer connections
- Exchange bindings

### Check Queue Status

```bash
docker exec rabbitmq rabbitmqctl list_queues name messages consumers
```

Expected output:
```
profile.events   0    1
comm.events      0    1
```

### Check Bindings

```bash
docker exec rabbitmq rabbitmqctl list_bindings
```

Should show bindings from `medtrack.events` exchange to queues.

---

## External Service Integration

External services (like your friend's microservice) can integrate by publishing events to RabbitMQ.

### Connection Details

```
Host: your-server-ip
Port: 5672
User: admin
Password: password
Exchange: medtrack.events
Type: topic
```

### Python Example

```python
import pika
import json
from datetime import datetime

# Connect to RabbitMQ
connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host='your-server-ip',
        port=5672,
        credentials=pika.PlainCredentials('admin', 'password')
    )
)
channel = connection.channel()

# Create event
event = {
    "event_type": "user.created",
    "payload": {
        "user_id": "uuid-from-your-system",
        "email": "newuser@example.com",
        "role": "student",  # or "encadrant"
        "first_name": "John",
        "last_name": "Doe"
    },
    "service": "external-service-name",
    "timestamp": datetime.utcnow().isoformat(),
    "version": "1.0"
}

# Publish event
channel.basic_publish(
    exchange='medtrack.events',
    routing_key='user.created',
    body=json.dumps(event),
    properties=pika.BasicProperties(
        delivery_mode=2,  # Persistent
        content_type='application/json'
    )
)

print("✅ Event published")
connection.close()
```

### Node.js Example

```javascript
const amqp = require('amqplib');

async function publishUserCreated() {
  const connection = await amqp.connect('amqp://admin:password@your-server-ip:5672');
  const channel = await connection.createChannel();

  const event = {
    event_type: 'user.created',
    payload: {
      user_id: 'uuid',
      email: 'newuser@example.com',
      role: 'student',
      first_name: 'John',
      last_name: 'Doe'
    },
    service: 'external-service',
    timestamp: new Date().toISOString(),
    version: '1.0'
  };

  channel.publish(
    'medtrack.events',
    'user.created',
    Buffer.from(JSON.stringify(event)),
    { persistent: true }
  );

  console.log('✅ Event published');
  await connection.close();
}
```

---

## Event Payload Specifications

### user.created

```json
{
  "event_type": "user.created",
  "payload": {
    "user_id": "uuid",          // Required
    "email": "string",          // Required
    "role": "student|encadrant",// Required - determines profile type
    "first_name": "string",     // Optional
    "last_name": "string",      // Optional
    "phone": "string",          // Optional
    "cin": "string"             // Optional
  },
  "service": "auth-service",
  "timestamp": "ISO-8601",
  "version": "1.0"
}
```

### student.created

```json
{
  "event_type": "student.created",
  "payload": {
    "student_id": "uuid",
    "user_id": "uuid",
    "email": "string",
    "cin": "string",
    "phone": "string",
    "first_name": "string",
    "last_name": "string",
    "created_at": "ISO-8601"
  },
  "service": "profile-service",
  "timestamp": "ISO-8601",
  "version": "1.0"
}
```

### stage.accepted

```json
{
  "event_type": "stage.accepted",
  "payload": {
    "stage_id": "uuid",
    "student_id": "uuid",
    "encadrant_id": "uuid",
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD",
    "accepted_at": "ISO-8601"
  },
  "service": "core-service",
  "timestamp": "ISO-8601",
  "version": "1.0"
}
```

---

## Implementation Status

### ✅ Complete (40%)
- ✅ **PROFILE-SERVICE** - Full event system (consume + publish)
- ✅ **COMM-SERVICE** - Full event system (consume + publish)
- ✅ **RabbitMQ Infrastructure** - Exchange, queues, bindings
- ✅ **Shared Event Library** - `shared/events.py`
- ✅ **Event Handlers** - PROFILE and COMM services

### 🔧 Infrastructure Ready (30%)
- 🔧 **AUTH-SERVICE** - RabbitMQ client ready, needs User models/views
- 🔧 **CORE-SERVICE** - RabbitMQ client ready, needs Offer/Stage models/views

### ⏭️ Not Started (30%)
- ⏭️ **EVAL-SERVICE** - Event system
- ⏭️ **Docker Compose** - Auto-start consumers
- ⏭️ **Integration Tests** - End-to-end event flow tests

---

## Next Steps

1. **Implement AUTH-SERVICE Controllers** (~30 min)
   - Create User model
   - Create registration/login endpoints
   - Add event publishing to controllers

2. **Implement CORE-SERVICE Controllers** (~45 min)
   - Create Offer/Stage models
   - Create REST API endpoints
   - Add event publishing to controllers

3. **Update Docker Compose** (~15 min)
   - Run consumers automatically
   - Add health checks for RabbitMQ

4. **Implement EVAL-SERVICE** (~1 hour)
   - Create Evaluation models
   - Add event publishing
   - Create event consumer

---

## Troubleshooting

### Events Not Being Consumed

**Check consumer is running:**
```bash
docker exec profile-service ps aux | grep consume_events
```

**Check RabbitMQ connection:**
```bash
docker logs profile-service | grep RabbitMQ
# Should see: "✅ RabbitMQ client initialized"
```

**Check queue exists:**
```bash
docker exec rabbitmq rabbitmqctl list_queues
# Should show: profile.events, comm.events
```

### Events Not Being Published

**Check RabbitMQ client initialized:**
```bash
docker logs <service-name> | grep "RabbitMQ client initialized"
```

**Check for publish errors:**
```bash
docker logs <service-name> | grep "Failed to publish"
```

### Queue Has Messages But Not Processed

**Check consumer errors:**
```bash
docker logs <service-name> -f | grep "Error processing event"
```

**Check message requeue:**
```bash
# In RabbitMQ UI, check "Redelivered" count
# High redelivered count = events failing to process
```

---

## Summary

This event-driven architecture provides:

✅ **Decoupled Services** - Services communicate only via events
✅ **Resilience** - Events queued if service down
✅ **Scalability** - Easy to add new consumers
✅ **Real-time** - WebSocket notifications to users
✅ **External Integration** - Easy for external services to publish events
✅ **Production Ready** - PROFILE and COMM services fully functional

**Current Status**: 40% complete. PROFILE-SERVICE and COMM-SERVICE are fully operational. AUTH-SERVICE and CORE-SERVICE need controller implementation to publish events.

For more details, see: `EXTERNAL_SERVICE_INTEGRATION_GUIDE.md`
