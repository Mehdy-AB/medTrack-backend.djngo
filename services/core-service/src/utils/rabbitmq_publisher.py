"""RabbitMQ message publisher for event-driven architecture."""
import os
import json
import pika
from typing import Dict, Any, Optional


class RabbitMQPublisher:
    """Publisher for sending messages to RabbitMQ."""
    
    def __init__(self):
        self.host = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
        self.port = int(os.environ.get('RABBITMQ_PORT', '5672'))
        self.user = os.environ.get('RABBITMQ_USER', 'guest')
        self.password = os.environ.get('RABBITMQ_PASSWORD', 'guest')
        self.connection = None
        self.channel = None
    
    def connect(self):
        """Establish connection to RabbitMQ."""
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
            return True
        except Exception as e:
            print(f"Error connecting to RabbitMQ: {e}")
            return False
    
    def close(self):
        """Close connection to RabbitMQ."""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
        except Exception as e:
            print(f"Error closing RabbitMQ connection: {e}")
    
    def publish_message(
        self,
        exchange: str,
        routing_key: str,
        message: Dict[Any, Any],
        exchange_type: str = 'topic'
    ) -> bool:
        """
        Publish a message to RabbitMQ.
        
        Args:
            exchange: Exchange name
            routing_key: Routing key for the message
            message: Message payload (will be JSON serialized)
            exchange_type: Type of exchange (topic, direct, fanout)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Connect if not already connected
            if not self.channel or self.connection.is_closed:
                if not self.connect():
                    return False
            
            # Declare exchange
            self.channel.exchange_declare(
                exchange=exchange,
                exchange_type=exchange_type,
                durable=True
            )
            
            # Serialize message
            message_body = json.dumps(message)
            
            # Publish message
            self.channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=message_body,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type='application/json'
                )
            )
            
            print(f"Published message to {exchange}/{routing_key}: {message}")
            return True
            
        except Exception as e:
            print(f"Error publishing message to RabbitMQ: {e}")
            return False
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Singleton instance
_publisher = None


def get_publisher() -> RabbitMQPublisher:
    """Get singleton RabbitMQ publisher."""
    global _publisher
    if _publisher is None:
        _publisher = RabbitMQPublisher()
    return _publisher


def publish_event(event_type: str, data: Dict[Any, Any]) -> bool:
    """
    Publish an event to RabbitMQ.
    
    Args:
        event_type: Type of event (e.g., 'application.accepted')
        data: Event payload
    
    Returns:
        True if successful, False otherwise
    """
    publisher = get_publisher()
    
    # Use 'events' exchange with event_type as routing key
    return publisher.publish_message(
        exchange='events',
        routing_key=event_type,
        message=data
    )
