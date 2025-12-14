"""RabbitMQ event publisher for EVAL-SERVICE."""
import os
import json
import pika
import uuid
from datetime import datetime
from typing import Dict, Any, Optional


class AttendanceEventPublisher:
    """RabbitMQ event publisher for attendance events."""
    
    # Event types
    ATTENDANCE_MARKED = 'eval.attendance.marked'
    ATTENDANCE_BULK_MARKED = 'eval.attendance.bulk_marked'
    ATTENDANCE_JUSTIFIED = 'eval.attendance.justified'
    ATTENDANCE_SUMMARY_UPDATED = 'eval.attendance.summary.updated'
    ATTENDANCE_VALIDATED = 'eval.attendance.validated'
    
    # Evaluation events
    EVALUATION_CREATED = 'eval.evaluation.created'
    EVALUATION_UPDATED = 'eval.evaluation.updated'
    EVALUATION_SUBMITTED = 'eval.evaluation.submitted'
    EVALUATION_VALIDATED = 'eval.evaluation.validated'
    EVALUATION_DELETED = 'eval.evaluation.deleted'
    
    def __init__(self):
        """Initialize RabbitMQ connection."""
        self.host = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
        self.port = int(os.environ.get('RABBITMQ_PORT', '5672'))
        self.exchange_name = 'medtrack.events'
        self.exchange_type = 'topic'
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
            
            # Declare topic exchange (durable) - same exchange as core-service
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
            event_type: Event routing key (e.g., 'eval.attendance.marked')
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
                'source': 'eval-service',
                'data': payload
            }
            
            # Publish with persistence
            self.channel.basic_publish(
                exchange=self.exchange_name,
                routing_key=event_type,
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
    
    def publish_attendance_marked(self, attendance_data: Dict[Any, Any]) -> bool:
        """Publish attendance.marked event."""
        return self.publish_event(self.ATTENDANCE_MARKED, attendance_data)
    
    def publish_attendance_bulk_marked(self, bulk_data: Dict[Any, Any]) -> bool:
        """Publish attendance.bulk_marked event."""
        return self.publish_event(self.ATTENDANCE_BULK_MARKED, bulk_data)
    
    def publish_attendance_justified(self, justification_data: Dict[Any, Any]) -> bool:
        """Publish attendance.justified event."""
        return self.publish_event(self.ATTENDANCE_JUSTIFIED, justification_data)
    
    def publish_attendance_summary_updated(self, summary_data: Dict[Any, Any]) -> bool:
        """Publish attendance.summary.updated event."""
        return self.publish_event(self.ATTENDANCE_SUMMARY_UPDATED, summary_data)
    
    def publish_attendance_validated(self, validation_data: Dict[Any, Any]) -> bool:
        """Publish attendance.validated event."""
        return self.publish_event(self.ATTENDANCE_VALIDATED, validation_data)
    
    def publish_evaluation_created(self, evaluation_data: Dict[Any, Any]) -> bool:
        """Publish evaluation.created event."""
        return self.publish_event(self.EVALUATION_CREATED, evaluation_data)
    
    def publish_evaluation_updated(self, evaluation_data: Dict[Any, Any]) -> bool:
        """Publish evaluation.updated event."""
        return self.publish_event(self.EVALUATION_UPDATED, evaluation_data)
    
    def publish_evaluation_submitted(self, evaluation_data: Dict[Any, Any]) -> bool:
        """Publish evaluation.submitted event."""
        return self.publish_event(self.EVALUATION_SUBMITTED, evaluation_data)
    
    def publish_evaluation_validated(self, validation_data: Dict[Any, Any]) -> bool:
        """Publish evaluation.validated event."""
        return self.publish_event(self.EVALUATION_VALIDATED, validation_data)
    
    def publish_evaluation_deleted(self, evaluation_id: str, student_id: str) -> bool:
        """Publish evaluation.deleted event."""
        return self.publish_event(self.EVALUATION_DELETED, {
            'evaluation_id': evaluation_id,
            'student_id': student_id
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


def get_attendance_publisher() -> AttendanceEventPublisher:
    """Get singleton AttendanceEventPublisher instance."""
    global _publisher
    if _publisher is None:
        _publisher = AttendanceEventPublisher()
    return _publisher
