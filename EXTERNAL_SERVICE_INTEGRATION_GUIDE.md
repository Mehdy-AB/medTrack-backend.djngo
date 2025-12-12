# External Service Integration Guide
## How to Integrate Your Microservice with MedTrack using RabbitMQ

---

## Overview

This guide shows external developers how to integrate their microservices with the MedTrack platform using event-driven communication via RabbitMQ.

**Key Principle**: Your service publishes events to RabbitMQ → MedTrack services automatically respond

---

## Setup

### 1. Connect to RabbitMQ

**Connection Details**:
- **Host**: `rabbitmq.medtrack.com` (or `localhost` for development)
- **Port**: `5672`
- **Username**: `admin`
- **Password**: `password`
- **Exchange**: `medtrack.events` (topic exchange)

### 2. Install RabbitMQ Client Library

**Python**:
```bash
pip install pika
```

**Node.js**:
```bash
npm install amqplib
```

**Java**:
```xml
<dependency>
    <groupId>com.rabbitmq</groupId>
    <artifactId>amqp-client</artifactId>
    <version>5.16.0</version>
</dependency>
```

---

## Publishing Events

### Python Example

```python
import pika
import json
from datetime import datetime

# Connect to RabbitMQ
credentials = pika.PlainCredentials('admin', 'password')
parameters = pika.ConnectionParameters(
    host='rabbitmq.medtrack.com',
    port=5672,
    credentials=credentials
)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

# Publish student.created event
event = {
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
    "service": "external-registration-service",
    "timestamp": datetime.utcnow().isoformat(),
    "version": "1.0"
}

channel.basic_publish(
    exchange='medtrack.events',
    routing_key='student.created',
    body=json.dumps(event),
    properties=pika.BasicProperties(
        delivery_mode=2,  # persistent
        content_type='application/json'
    )
)

print("✅ Event published!")
connection.close()
```

### Node.js Example

```javascript
const amqp = require('amqplib');

async function publishStudentCreated(studentData) {
    // Connect to RabbitMQ
    const connection = await amqp.connect({
        protocol: 'amqp',
        hostname: 'rabbitmq.medtrack.com',
        port: 5672,
        username: 'admin',
        password: 'password'
    });

    const channel = await connection.createChannel();

    // Create event
    const event = {
        event_type: 'student.created',
        payload: {
            student_id: studentData.id,
            user_id: studentData.userId,
            cin: studentData.cin,
            email: studentData.email,
            phone: studentData.phone,
            first_name: studentData.firstName,
            last_name: studentData.lastName
        },
        service: 'external-registration-service',
        timestamp: new Date().toISOString(),
        version: '1.0'
    };

    // Publish to exchange
    channel.publish(
        'medtrack.events',          // exchange
        'student.created',           // routing key
        Buffer.from(JSON.dumps(event)),
        { persistent: true, contentType: 'application/json' }
    );

    console.log('✅ Event published!');

    await channel.close();
    await connection.close();
}

// Usage
publishStudentCreated({
    id: '550e8400-e29b-41d4-a716-446655440000',
    userId: '660e9500-f39c-52e5-b827-557766551111',
    cin: 'AB123456',
    email: 'student@example.com',
    phone: '+1234567890',
    firstName: 'John',
    lastName: 'Doe'
});
```

### Java Example

```java
import com.rabbitmq.client.*;
import org.json.JSONObject;
import java.time.Instant;

public class EventPublisher {
    private static final String EXCHANGE = "medtrack.events";
    private static final String HOST = "rabbitmq.medtrack.com";

    public static void publishStudentCreated(Student student) throws Exception {
        ConnectionFactory factory = new ConnectionFactory();
        factory.setHost(HOST);
        factory.setPort(5672);
        factory.setUsername("admin");
        factory.setPassword("password");

        try (Connection connection = factory.newConnection();
             Channel channel = connection.createChannel()) {

            // Create event JSON
            JSONObject event = new JSONObject();
            event.put("event_type", "student.created");

            JSONObject payload = new JSONObject();
            payload.put("student_id", student.getId());
            payload.put("user_id", student.getUserId());
            payload.put("cin", student.getCin());
            payload.put("email", student.getEmail());
            payload.put("phone", student.getPhone());
            payload.put("first_name", student.getFirstName());
            payload.put("last_name", student.getLastName());
            event.put("payload", payload);

            event.put("service", "external-registration-service");
            event.put("timestamp", Instant.now().toString());
            event.put("version", "1.0");

            // Publish event
            AMQP.BasicProperties props = new AMQP.BasicProperties.Builder()
                    .deliveryMode(2)  // persistent
                    .contentType("application/json")
                    .build();

            channel.basicPublish(
                EXCHANGE,
                "student.created",
                props,
                event.toString().getBytes()
            );

            System.out.println("✅ Event published!");
        }
    }
}
```

---

## Event Types You Can Publish

### 1. Student Events

#### student.created
```json
{
    "event_type": "student.created",
    "payload": {
        "student_id": "uuid",
        "user_id": "uuid",
        "cin": "AB123456",
        "email": "student@example.com",
        "phone": "+1234567890",
        "first_name": "John",
        "last_name": "Doe"
    },
    "service": "your-service-name",
    "timestamp": "2025-01-15T10:00:00Z",
    "version": "1.0"
}
```

**What Happens**:
- ✅ COMM-SERVICE sends welcome notification to student
- ✅ AUTH-SERVICE may create user account (if not exists)
- ✅ CORE-SERVICE initializes stage tracking

#### student.updated
```json
{
    "event_type": "student.updated",
    "payload": {
        "student_id": "uuid",
        "updated_fields": ["email", "phone"]
    },
    "service": "your-service-name",
    "timestamp": "2025-01-15T10:00:00Z",
    "version": "1.0"
}
```

#### student.deleted
```json
{
    "event_type": "student.deleted",
    "payload": {
        "student_id": "uuid",
        "user_id": "uuid"
    },
    "service": "your-service-name",
    "timestamp": "2025-01-15T10:00:00Z",
    "version": "1.0"
}
```

### 2. User Events

#### user.created
```json
{
    "event_type": "user.created",
    "payload": {
        "user_id": "uuid",
        "email": "user@example.com",
        "role": "student",
        "first_name": "John",
        "last_name": "Doe"
    },
    "service": "your-service-name",
    "timestamp": "2025-01-15T10:00:00Z",
    "version": "1.0"
}
```

**What Happens**:
- ✅ PROFILE-SERVICE may create profile
- ✅ COMM-SERVICE logs the creation

### 3. Stage Events

#### stage.created
```json
{
    "event_type": "stage.created",
    "payload": {
        "stage_id": "uuid",
        "student_id": "uuid",
        "offer_id": "uuid",
        "start_date": "2025-02-01"
    },
    "service": "your-service-name",
    "timestamp": "2025-01-15T10:00:00Z",
    "version": "1.0"
}
```

**What Happens**:
- ✅ COMM-SERVICE notifies student
- ✅ EVAL-SERVICE creates evaluation template

#### stage.accepted
```json
{
    "event_type": "stage.accepted",
    "payload": {
        "stage_id": "uuid",
        "student_id": "uuid",
        "encadrant_id": "uuid",
        "start_date": "2025-02-01"
    },
    "service": "your-service-name",
    "timestamp": "2025-01-15T10:00:00Z",
    "version": "1.0"
}
```

**What Happens**:
- ✅ COMM-SERVICE sends congratulations notification
- ✅ Email notification sent to student

### 4. Evaluation Events

#### evaluation.created
```json
{
    "event_type": "evaluation.created",
    "payload": {
        "evaluation_id": "uuid",
        "stage_id": "uuid",
        "student_id": "uuid",
        "score": 85
    },
    "service": "your-service-name",
    "timestamp": "2025-01-15T10:00:00Z",
    "version": "1.0"
}
```

**What Happens**:
- ✅ COMM-SERVICE notifies student of evaluation
- ✅ Score saved to student record

---

## Complete Integration Example

### Scenario: External Registration System

Your system handles student registration. When a student registers:

```python
# your_service.py
import pika
import json
from datetime import datetime

class MedTrackEventPublisher:
    def __init__(self, host='rabbitmq.medtrack.com'):
        credentials = pika.PlainCredentials('admin', 'password')
        parameters = pika.ConnectionParameters(
            host=host,
            port=5672,
            credentials=credentials
        )
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()

    def publish_event(self, event_type, payload):
        event = {
            "event_type": event_type,
            "payload": payload,
            "service": "external-registration-service",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0"
        }

        self.channel.basic_publish(
            exchange='medtrack.events',
            routing_key=event_type,
            body=json.dumps(event),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type='application/json'
            )
        )

        print(f"✅ Published: {event_type}")

    def close(self):
        self.connection.close()


# Usage in your application
def register_student(student_data):
    # 1. Save student to YOUR database
    student = YourDatabase.save(student_data)

    # 2. Publish event to MedTrack
    publisher = MedTrackEventPublisher()

    # First, create user
    publisher.publish_event(
        event_type='user.created',
        payload={
            'user_id': student.user_id,
            'email': student.email,
            'role': 'student',
            'first_name': student.first_name,
            'last_name': student.last_name
        }
    )

    # Then, create student profile
    publisher.publish_event(
        event_type='student.created',
        payload={
            'student_id': student.id,
            'user_id': student.user_id,
            'cin': student.cin,
            'email': student.email,
            'phone': student.phone,
            'first_name': student.first_name,
            'last_name': student.last_name
        }
    )

    publisher.close()

    # 3. MedTrack automatically:
    #    - Sends welcome notification to student
    #    - Creates profile in PROFILE-SERVICE
    #    - Initializes stage tracking

    return student
```

---

## Consuming Events from MedTrack

If you want to receive events FROM MedTrack (e.g., when a stage is completed):

### Python Consumer

```python
import pika
import json

def handle_event(event):
    """Process incoming event"""
    event_type = event['event_type']
    payload = event['payload']

    if event_type == 'stage.completed':
        student_id = payload['student_id']
        completion_date = payload['completion_date']
        # Update your system
        print(f"Stage completed for student {student_id}")

# Connect to RabbitMQ
credentials = pika.PlainCredentials('admin', 'password')
parameters = pika.ConnectionParameters(
    host='rabbitmq.medtrack.com',
    port=5672,
    credentials=credentials
)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

# Declare your queue
queue_name = 'your-service.events'
channel.queue_declare(queue=queue_name, durable=True)

# Bind to events you care about
channel.queue_bind(
    exchange='medtrack.events',
    queue=queue_name,
    routing_key='stage.*'  # All stage events
)

# Start consuming
def callback(ch, method, properties, body):
    event = json.loads(body)
    handle_event(event)
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue=queue_name, on_message_callback=callback)

print('🔄 Consuming events...')
channel.start_consuming()
```

---

## Testing

### Test Event Publishing

```bash
# Using RabbitMQ Management API
curl -X POST http://rabbitmq.medtrack.com:15672/api/exchanges/%2F/medtrack.events/publish \
  -u admin:password \
  -H "Content-Type: application/json" \
  -d '{
    "properties": {"delivery_mode": 2, "content_type": "application/json"},
    "routing_key": "student.created",
    "payload": "{\"event_type\":\"student.created\",\"payload\":{\"student_id\":\"test-123\",\"email\":\"test@example.com\"},\"service\":\"test\"}",
    "payload_encoding": "string"
  }'
```

### Monitor Events in RabbitMQ UI

1. Go to: `http://rabbitmq.medtrack.com:15672`
2. Login: `admin` / `password`
3. Click "Queues" to see all queues
4. Click a queue to see messages
5. Click "Get messages" to view event payloads

---

## Error Handling

### If Event Publishing Fails

- **Check connection**: Is RabbitMQ running and accessible?
- **Check credentials**: Are username/password correct?
- **Check exchange**: Is `medtrack.events` declared?
- **Check payload**: Is JSON valid?

### Retry Logic Example

```python
import time

def publish_with_retry(event_type, payload, max_retries=3):
    for attempt in range(max_retries):
        try:
            publisher = MedTrackEventPublisher()
            publisher.publish_event(event_type, payload)
            publisher.close()
            return True
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                print("❌ All retries failed")
                return False
```

---

## Benefits for Your Service

✅ **Decoupled**: Your service doesn't need to know MedTrack's API
✅ **Resilient**: Events are queued if MedTrack is down
✅ **Async**: No waiting for HTTP responses
✅ **Scalable**: Add more consumers without changing your code
✅ **Auditable**: All events are logged in RabbitMQ

---

## Support

Questions? Contact the MedTrack team or check the full event documentation at:
`https://github.com/medtrack/docs/events`
