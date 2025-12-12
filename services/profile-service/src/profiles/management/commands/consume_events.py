"""
Django management command to consume RabbitMQ events for PROFILE-SERVICE

Usage:
    python manage.py consume_events

This command will:
    1. Connect to RabbitMQ
    2. Declare the queue 'profile.events'
    3. Subscribe to user events from AUTH-SERVICE or external services
    4. Automatically create student/encadrant profiles when users are created
    5. Run forever until stopped (Ctrl+C)
"""
import os
import logging
from django.core.management.base import BaseCommand
from profiles.events import get_rabbitmq_client
from profiles.event_handlers import route_event

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Consume RabbitMQ events for PROFILE-SERVICE'

    def add_arguments(self, parser):
        parser.add_argument(
            '--queue',
            type=str,
            default='profile.events',
            help='Queue name to consume from (default: profile.events)'
        )

    def handle(self, *args, **options):
        queue_name = options['queue']

        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('🚀 PROFILE-SERVICE Event Consumer'))
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
            # PROFILE-SERVICE listens for user events to auto-create profiles
            routing_keys = [
                'user.created',      # When user is created, create student/encadrant profile
                'user.deleted',      # When user is deleted, delete associated profiles
                'user.verified',     # Could update profile verification status
            ]

            self.stdout.write(f"📥 Declaring queue: {queue_name}")
            self.stdout.write(f"🔗 Binding to routing keys: {', '.join(routing_keys)}")
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('📌 Automatic Profile Creation:'))
            self.stdout.write('   • user.created (role=student) → creates Student profile')
            self.stdout.write('   • user.created (role=encadrant) → creates Encadrant profile')
            self.stdout.write('')

            rabbitmq.declare_queue(
                queue_name=queue_name,
                routing_keys=routing_keys
            )

            self.stdout.write(self.style.SUCCESS('✅ Consumer ready!'))
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
