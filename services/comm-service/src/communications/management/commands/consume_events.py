"""
Django management command to consume RabbitMQ events for COMM-SERVICE

Usage:
    python manage.py consume_events

This command will:
    1. Connect to RabbitMQ
    2. Declare the queue 'comm.events'
    3. Subscribe to relevant event patterns
    4. Process events as they arrive
    5. Run forever until stopped (Ctrl+C)
"""
import os
import logging
from django.core.management.base import BaseCommand
from communications.events import get_rabbitmq_client
from communications.event_handlers import route_event

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Consume RabbitMQ events for COMM-SERVICE'

    def add_arguments(self, parser):
        parser.add_argument(
            '--queue',
            type=str,
            default='comm.events',
            help='Queue name to consume from (default: comm.events)'
        )

    def handle(self, *args, **options):
        queue_name = options['queue']

        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('🚀 COMM-SERVICE Event Consumer'))
        self.stdout.write(self.style.SUCCESS('=' * 80))

        # Get RabbitMQ connection details from environment
        rabbitmq_host = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
        rabbitmq_port = int(os.environ.get('RABBITMQ_PORT', 5672))
        rabbitmq_user = os.environ.get('RABBITMQ_USER', 'admin')
        rabbitmq_password = os.environ.get('RABBITMQ_PASSWORD', 'password')

        self.stdout.write(f"📡 Connecting to RabbitMQ at {rabbitmq_host}:{rabbitmq_port}")

        try:
            # Initialize RabbitMQ client
            rabbitmq = get_rabbitmq_client(
                host=rabbitmq_host,
                port=rabbitmq_port,
                user=rabbitmq_user,
                password=rabbitmq_password
            )

            # Declare queue and routing bindings
            routing_keys = [
                'student.*',        # All student events (created, updated, deleted)
                'encadrant.*',      # All encadrant events
                'stage.*',          # All stage events (created, accepted, completed, etc.)
                'evaluation.*',     # All evaluation events
                'user.created',     # Specific user event
                'offer.created',    # New offer events
                'grade.*'           # Grade events
            ]

            self.stdout.write(f"📥 Declaring queue: {queue_name}")
            self.stdout.write(f"🔗 Binding to routing keys: {', '.join(routing_keys)}")

            rabbitmq.declare_queue(
                queue_name=queue_name,
                routing_keys=routing_keys
            )

            self.stdout.write(self.style.SUCCESS('\n✅ Consumer ready!'))
            self.stdout.write('📨 Waiting for events... (Press CTRL+C to stop)\n')

            # Start consuming events
            rabbitmq.consume_events(
                queue_name=queue_name,
                callback=route_event
            )

        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\n\n⛔ Consumer stopped by user'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n\n❌ Error: {e}'))
            logger.error(f"Event consumer error: {e}", exc_info=True)
            raise

        finally:
            self.stdout.write(self.style.SUCCESS('\n👋 Consumer shutdown complete'))
