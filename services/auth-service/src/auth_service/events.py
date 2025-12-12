"""
RabbitMQ event publisher for auth-service.
Publishes user-related events to events.topic exchange.
"""
import json
import pika
import logging
from datetime import datetime, timezone
from django.conf import settings
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class EventPublisher:
    """Publishes events to RabbitMQ."""

    EXCHANGE_NAME = 'events.topic'
    EXCHANGE_TYPE = 'topic'

    # Event types
    USER_CREATED = 'auth.user.created'
    USER_UPDATED = 'auth.user.updated'
    USER_ROLE_CHANGED = 'auth.user.role_changed'
    SESSION_REVOKED = 'auth.session.revoked'
    PASSWORD_CHANGED = 'auth.password.changed'
    USER_DELETED = 'auth.user.deleted'

    def __init__(self):
        self._connection = None
        self._channel = None

    def _get_connection_params(self) -> pika.ConnectionParameters:
        """Get RabbitMQ connection parameters from settings."""
        return pika.ConnectionParameters(
            host=getattr(settings, 'RABBITMQ_HOST', 'rabbitmq'),
            port=getattr(settings, 'RABBITMQ_PORT', 5672),
            credentials=pika.PlainCredentials(
                getattr(settings, 'RABBITMQ_USER', 'admin'),
                getattr(settings, 'RABBITMQ_PASSWORD', 'password')
            ),
            virtual_host=getattr(settings, 'RABBITMQ_VHOST', '/'),
            connection_attempts=3,
            retry_delay=2,
        )

    def _ensure_connection(self) -> None:
        """Ensure RabbitMQ connection is established."""
        try:
            if self._connection is None or self._connection.is_closed:
                self._connection = pika.BlockingConnection(
                    self._get_connection_params()
                )
                self._channel = self._connection.channel()

                # Declare exchange
                self._channel.exchange_declare(
                    exchange=self.EXCHANGE_NAME,
                    exchange_type=self.EXCHANGE_TYPE,
                    durable=True
                )
        except pika.exceptions.AMQPError as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            self._connection = None
            self._channel = None
            raise

    def publish(self, routing_key: str, message: Dict[str, Any]) -> bool:
        """
        Publish message to RabbitMQ.

        Args:
            routing_key: Routing key (e.g., 'auth.user.created')
            message: Message payload as dictionary

        Returns:
            True if published successfully, False otherwise
        """
        try:
            self._ensure_connection()

            # Add metadata to message
            message['_meta'] = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'routing_key': routing_key,
                'source': 'auth-service',
            }

            self._channel.basic_publish(
                exchange=self.EXCHANGE_NAME,
                routing_key=routing_key,
                body=json.dumps(message, default=str),
                properties=pika.BasicProperties(
                    content_type='application/json',
                    delivery_mode=2,  # Persistent
                )
            )

            logger.info(f"Published event: {routing_key}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish event {routing_key}: {e}")
            return False

    def close(self) -> None:
        """Close RabbitMQ connection."""
        if self._connection and not self._connection.is_closed:
            self._connection.close()
            self._connection = None
            self._channel = None


# Global publisher instance
_publisher: Optional[EventPublisher] = None


def get_publisher() -> EventPublisher:
    """Get or create global event publisher."""
    global _publisher
    if _publisher is None:
        _publisher = EventPublisher()
    return _publisher


def publish_user_created(user) -> bool:
    """Publish USER_CREATED event."""
    return get_publisher().publish(
        EventPublisher.USER_CREATED,
        {
            'event_type': 'USER_CREATED',
            'user_id': str(user.id),
            'email': user.email,
            'role': user.role,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
    )


def publish_user_updated(user, changed_fields: list = None) -> bool:
    """Publish USER_UPDATED event."""
    return get_publisher().publish(
        EventPublisher.USER_UPDATED,
        {
            'event_type': 'USER_UPDATED',
            'user_id': str(user.id),
            'email': user.email,
            'changed_fields': changed_fields or [],
        }
    )


def publish_user_role_changed(user, old_role: str, new_role: str) -> bool:
    """Publish USER_ROLE_CHANGED event."""
    return get_publisher().publish(
        EventPublisher.USER_ROLE_CHANGED,
        {
            'event_type': 'USER_ROLE_CHANGED',
            'user_id': str(user.id),
            'email': user.email,
            'old_role': old_role,
            'new_role': new_role,
        }
    )


def publish_session_revoked(session, user) -> bool:
    """Publish SESSION_REVOKED event."""
    return get_publisher().publish(
        EventPublisher.SESSION_REVOKED,
        {
            'event_type': 'SESSION_REVOKED',
            'session_id': str(session.id),
            'user_id': str(user.id),
        }
    )


def publish_password_changed(user) -> bool:
    """Publish PASSWORD_CHANGED event."""
    return get_publisher().publish(
        EventPublisher.PASSWORD_CHANGED,
        {
            'event_type': 'PASSWORD_CHANGED',
            'user_id': str(user.id),
            'email': user.email,
        }
    )


def publish_user_deleted(user_id: str, email: str) -> bool:
    """Publish USER_DELETED event."""
    return get_publisher().publish(
        EventPublisher.USER_DELETED,
        {
            'event_type': 'USER_DELETED',
            'user_id': user_id,
            'email': email,
        }
    )
