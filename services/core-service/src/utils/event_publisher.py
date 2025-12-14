"""Enhanced RabbitMQ publisher for Core-Service events."""
import os
import json
import pika
import uuid
from datetime import datetime
from typing import Dict, Any, Optional


class EventPublisher:
    """RabbitMQ event publisher with topic exchange."""
    
    # Event types
    # Offer events
    OFFER_CREATED = 'core.offer.created'
    OFFER_PUBLISHED = 'core.offer.published'
    OFFER_UPDATED = 'core.offer.updated'
    OFFER_CLOSED = 'core.offer.closed'
    OFFER_DELETED = 'core.offer.deleted'
    
    # Application events
    APPLICATION_SUBMITTED = 'core.application.submitted'
    APPLICATION_UPDATED = 'core.application.updated'
    APPLICATION_WITHDRAWN = 'core.application.withdrawn'
    APPLICATION_ACCEPTED = 'core.application.accepted'
    APPLICATION_REJECTED = 'core.application.rejected'
    
    # Affectation events
    AFFECTATION_CREATED = 'core.affectation.created'
    AFFECTATION_UPDATED = 'core.affectation.updated'
    AFFECTATION_DELETED = 'core.affectation.deleted'
    
    def __init__(self):
        """Initialize RabbitMQ connection."""
        self.host = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
        self.port = int(os.environ.get('RABBITMQ_PORT', '5672'))
        self.exchange_name = 'medtrack.events'
        self.exchange_type = 'topic'  # Topic exchange for flexible routing
        self.connection = None
        self.channel = None
    
    def connect(self):
        """Establish connection to RabbitMQ."""
        try:
            credentials = pika.PlainCredentials('admin', 'password')  # Changed from 'guest', 'guest'
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare topic exchange (durable)
            self.channel.exchange_declare(
                exchange=self.exchange_name,
                exchange_type=self.exchange_type,
                durable=True
            )
            
            return True
        except Exception as e:
            print(f"Failed to connect to RabbitMQ: {e}")
            return False
    
    def publish_event(
        self,
        event_type: str,
        payload: Dict[Any, Any],
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Publish an event to RabbitMQ.
        
        Args:
            event_type: Event routing key (e.g., 'core.offer.created')
            payload: Event data (will be JSON serialized)
            correlation_id: Optional ID for tracking related events
        
        Returns:
            True if published successfully, False otherwise
        """
        try:
            if not self.connection or self.connection.is_closed:
                if not self.connect():
                    return False
            
            # Create event envelope
            event = {
                'event_id': str(uuid.uuid4()),
                'event_type': event_type,
                'timestamp': datetime.utcnow().isoformat(),
                'correlation_id': correlation_id or str(uuid.uuid4()),
                'source': 'core-service',
                'data': payload
            }
            
            # Publish with persistence
            self.channel.basic_publish(
                exchange=self.exchange_name,
                routing_key=event_type,  # Topic routing key
                body=json.dumps(event),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Persistent message
                    content_type='application/json',
                    correlation_id=event['correlation_id']
                )
            )
            
            print(f"✅ Published event: {event_type} (ID: {event['event_id']})")
            return True
            
        except Exception as e:
            print(f"❌ Failed to publish event {event_type}: {e}")
            return False
    
    def publish_offer_created(self, offer_data: Dict[Any, Any]) -> bool:
        """Publish offer.created event."""
        return self.publish_event(self.OFFER_CREATED, offer_data)
    
    def publish_offer_published(self, offer_data: Dict[Any, Any]) -> bool:
        """Publish offer.published event."""
        return self.publish_event(self.OFFER_PUBLISHED, offer_data)
    
    def publish_offer_updated(self, offer_data: Dict[Any, Any]) -> bool:
        """Publish offer.updated event."""
        return self.publish_event(self.OFFER_UPDATED, offer_data)
    
    def publish_offer_closed(self, offer_data: Dict[Any, Any]) -> bool:
        """Publish offer.closed event."""
        return self.publish_event(self.OFFER_CLOSED, offer_data)
    
    def publish_offer_deleted(self, offer_id: str) -> bool:
        """Publish offer.deleted event."""
        return self.publish_event(self.OFFER_DELETED, {'offer_id': offer_id})
    
    def publish_application_submitted(self, application_data: Dict[Any, Any]) -> bool:
        """Publish application.submitted event."""
        return self.publish_event(self.APPLICATION_SUBMITTED, application_data)
    
    def publish_application_updated(self, application_data: Dict[Any, Any]) -> bool:
        """Publish application.updated event."""
        return self.publish_event(self.APPLICATION_UPDATED, application_data)
    
    def publish_application_withdrawn(self, application_data: Dict[Any, Any]) -> bool:
        """Publish application.withdrawn event."""
        return self.publish_event(self.APPLICATION_WITHDRAWN, application_data)
    
    def publish_application_accepted(self, application_data: Dict[Any, Any]) -> bool:
        """Publish application.accepted event."""
        return self.publish_event(self.APPLICATION_ACCEPTED, application_data)
    
    def publish_application_rejected(self, application_data: Dict[Any, Any]) -> bool:
        """Publish application.rejected event."""
        return self.publish_event(self.APPLICATION_REJECTED, application_data)
    
    def publish_affectation_created(self, affectation_data: Dict[Any, Any]) -> bool:
        """Publish affectation.created event."""
        return self.publish_event(self.AFFECTATION_CREATED, affectation_data)
    
    def publish_affectation_updated(self, affectation_data: Dict[Any, Any]) -> bool:
        """Publish affectation.updated event."""
        return self.publish_event(self.AFFECTATION_UPDATED, affectation_data)
    
    def publish_affectation_deleted(self, affectation_id: str, student_id: str, offer_id: str) -> bool:
        """Publish affectation.deleted event."""
        return self.publish_event(self.AFFECTATION_DELETED, {
            'affectation_id': affectation_id,
            'student_id': student_id,
            'offer_id': offer_id
        })
    
    def close(self):
        """Close RabbitMQ connection."""
        try:
            if self.channel and not self.channel.is_closed:
                self.channel.close()
            if self.connection and not self.connection.is_closed:
                self.connection.close()
        except Exception as e:
            print(f"Error closing RabbitMQ connection: {e}")


# Singleton instance
_publisher = None


def get_event_publisher() -> EventPublisher:
    """Get singleton EventPublisher instance."""
    global _publisher
    if _publisher is None:
        _publisher = EventPublisher()
    return _publisher
