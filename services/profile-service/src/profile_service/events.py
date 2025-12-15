"""
Shared event definitions and RabbitMQ utilities for MedTrack microservices
Copy this file to each microservice's src directory
"""
import json
import logging
import pika
from typing import Dict, Any, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


# ============================================
# EVENT TYPE DEFINITIONS
# ============================================

class EventTypes:
    """All event types in the system"""

    # AUTH-SERVICE events
    USER_CREATED = "user.created"
    USER_VERIFIED = "user.verified"
    USER_PASSWORD_CHANGED = "user.password_changed"
    USER_DELETED = "user.deleted"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"

    # PROFILE-SERVICE events
    STUDENT_CREATED = "student.created"
    STUDENT_UPDATED = "student.updated"
    STUDENT_DELETED = "student.deleted"
    ENCADRANT_CREATED = "encadrant.created"
    ENCADRANT_UPDATED = "encadrant.updated"
    ENCADRANT_DELETED = "encadrant.deleted"
    ESTABLISHMENT_CREATED = "establishment.created"
    ESTABLISHMENT_UPDATED = "establishment.updated"
    SERVICE_CREATED = "service.created"
    SERVICE_UPDATED = "service.updated"

    # CORE-SERVICE events
    OFFER_CREATED = "offer.created"
    OFFER_UPDATED = "offer.updated"
    OFFER_DELETED = "offer.deleted"
    STAGE_CREATED = "stage.created"
    STAGE_ACCEPTED = "stage.accepted"
    STAGE_REJECTED = "stage.rejected"
    STAGE_STARTED = "stage.started"
    STAGE_COMPLETED = "stage.completed"
    STAGE_CANCELLED = "stage.cancelled"

    # COMM-SERVICE events
    MESSAGE_SENT = "message.sent"
    MESSAGE_READ = "message.read"
    NOTIFICATION_CREATED = "notification.created"
    DOCUMENT_UPLOADED = "document.uploaded"
    DOCUMENT_DELETED = "document.deleted"
    EMAIL_SENT = "email.sent"
    EMAIL_FAILED = "email.failed"

    # EVAL-SERVICE events
    EVALUATION_CREATED = "evaluation.created"
    EVALUATION_UPDATED = "evaluation.updated"
    EVALUATION_DELETED = "evaluation.deleted"
    GRADE_ASSIGNED = "grade.assigned"
    ATTENDANCE_MARKED = "attendance.marked"


# ============================================
# RABBITMQ CLIENT
# ============================================

class RabbitMQClient:
    """
    RabbitMQ client for publishing and consuming events

    Usage:
        # Publish an event
        rabbitmq = RabbitMQClient(host='rabbitmq', port=5672, user='admin', password='password')
        rabbitmq.connect()
        rabbitmq.publish_event('student.created', {'student_id': '123'}, 'profile-service')

        # Consume events
        def my_handler(event):
            print(f"Received: {event}")

        rabbitmq.declare_queue('my-service.events', ['student.*', 'user.created'])
        rabbitmq.consume_events('my-service.events', my_handler)
    """

    EXCHANGE_NAME = "medtrack.events"
    EXCHANGE_TYPE = "topic"

    def __init__(self, host: str, port: int, user: str, password: str):
        """
        Initialize RabbitMQ client

        Args:
            host: RabbitMQ host
            port: RabbitMQ port (usually 5672)
            user: RabbitMQ username
            password: RabbitMQ password
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.connection = None
        self.channel = None

    def connect(self):
        """Establish connection to RabbitMQ"""
        try:
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

            # Declare exchange (topic exchange for routing)
            self.channel.exchange_declare(
                exchange=self.EXCHANGE_NAME,
                exchange_type=self.EXCHANGE_TYPE,
                durable=True
            )

            logger.info(f"✅ Connected to RabbitMQ at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to RabbitMQ: {e}")
            raise

    def publish_event(self, event_type: str, payload: Dict[str, Any], service_name: str):
        """
        Publish an event to RabbitMQ

        Args:
            event_type: Event type (routing key) - e.g., "student.created"
            payload: Event data as dictionary
            service_name: Name of the service publishing the event

        Example:
            rabbitmq.publish_event(
                event_type=EventTypes.STUDENT_CREATED,
                payload={'student_id': '123', 'email': 'student@example.com'},
                service_name='profile-service'
            )
        """
        if not self.channel:
            self.connect()

        # Create event envelope
        event = {
            "event_type": event_type,
            "payload": payload,
            "service": service_name,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0"
        }

        message = json.dumps(event)

        try:
            self.channel.basic_publish(
                exchange=self.EXCHANGE_NAME,
                routing_key=event_type,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type="application/json"
                )
            )

            logger.info(f"📤 Published event: {event_type} from {service_name}")
        except Exception as e:
            logger.error(f"❌ Failed to publish event {event_type}: {e}")
            raise

    def declare_queue(self, queue_name: str, routing_keys: list):
        """
        Declare a queue and bind it to routing keys

        Args:
            queue_name: Name of the queue (e.g., 'comm.events')
            routing_keys: List of routing patterns to subscribe to
                         - Use exact match: "user.created"
                         - Use wildcard: "student.*" (all student events)
                         - Use multi-wildcard: "*.created" (all created events)

        Example:
            rabbitmq.declare_queue('comm.events', ['student.*', 'stage.*', 'user.created'])
        """
        if not self.channel:
            self.connect()

        # Declare durable queue (survives RabbitMQ restart)
        self.channel.queue_declare(queue=queue_name, durable=True)

        # Bind queue to exchange with routing keys
        for routing_key in routing_keys:
            self.channel.queue_bind(
                exchange=self.EXCHANGE_NAME,
                queue=queue_name,
                routing_key=routing_key
            )

        logger.info(f"📥 Queue '{queue_name}' declared with bindings: {routing_keys}")

    def consume_events(self, queue_name: str, callback: Callable[[Dict], None]):
        """
        Start consuming events from a queue

        Args:
            queue_name: Name of the queue to consume from
            callback: Function to call for each event - receives event dict

        Example:
            def my_handler(event):
                event_type = event['event_type']
                payload = event['payload']
                print(f"Got event: {event_type} with data: {payload}")

            rabbitmq.consume_events('comm.events', my_handler)
        """
        if not self.channel:
            self.connect()

        def on_message(ch, method, properties, body):
            """Internal message handler"""
            try:
                event = json.loads(body)
                event_type = event.get('event_type', 'unknown')

                logger.info(f"📨 Received event: {event_type}")

                # Call the user's callback
                callback(event)

                # Acknowledge message (remove from queue)
                ch.basic_ack(delivery_tag=method.delivery_tag)

            except Exception as e:
                logger.error(f"❌ Error processing event: {e}")
                # Reject and requeue message (will be retried)
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        # Process one message at a time (important for reliability)
        self.channel.basic_qos(prefetch_count=1)

        # Start consuming
        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=on_message
        )

        logger.info(f"🔄 Starting event consumer for queue: {queue_name}")
        logger.info("Press CTRL+C to stop")

        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("⛔ Consumer stopped by user")
            self.stop_consuming()

    def stop_consuming(self):
        """Stop consuming events"""
        if self.channel:
            self.channel.stop_consuming()

    def close(self):
        """Close RabbitMQ connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("🔌 RabbitMQ connection closed")


# ============================================
# SINGLETON INSTANCE
# ============================================

_rabbitmq_client = None


def get_rabbitmq_client(host: str = None, port: int = None, user: str = None, password: str = None) -> RabbitMQClient:
    """
    Get or create RabbitMQ client singleton

    Args:
        host: RabbitMQ host (optional, uses existing if None)
        port: RabbitMQ port (optional)
        user: RabbitMQ user (optional)
        password: RabbitMQ password (optional)

    Returns:
        RabbitMQClient instance

    Example:
        # First call - creates client
        rabbitmq = get_rabbitmq_client('rabbitmq', 5672, 'admin', 'password')

        # Subsequent calls - returns same instance
        rabbitmq = get_rabbitmq_client()
    """
    global _rabbitmq_client

    if _rabbitmq_client is None:
        if not all([host, port, user, password]):
            # Try to get from settings if django is present
            try:
                from django.conf import settings
                host = getattr(settings, 'RABBITMQ_HOST', None)
                port = getattr(settings, 'RABBITMQ_PORT', None)
                user = getattr(settings, 'RABBITMQ_USER', None)
                password = getattr(settings, 'RABBITMQ_PASSWORD', None)
            except ImportError:
                pass
        
        if not all([host, port, user, password]):
             raise ValueError("First call to get_rabbitmq_client requires all parameters")

        _rabbitmq_client = RabbitMQClient(host, int(port) if port else 5672, user, password)
        _rabbitmq_client.connect()

    return _rabbitmq_client


# ============================================
# HELPER FUNCTIONS
# ============================================

def publish_event(event_type: str, payload: Dict[str, Any], service_name: str):
    """
    Convenience function to publish an event using the singleton client

    Example:
        from events import publish_event, EventTypes

        publish_event(
            event_type=EventTypes.STUDENT_CREATED,
            payload={'student_id': str(student.id), 'email': student.email},
            service_name='profile-service'
        )
    """
    client = get_rabbitmq_client()
    client.publish_event(event_type, payload, service_name)
