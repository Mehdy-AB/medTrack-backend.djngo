"""RabbitMQ consumer for EVAL-SERVICE - Attendance creation."""
import os
import sys
import json
import pika
import django
from time import sleep

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eval_service.settings')
django.setup()

from attendance.models import AttendanceRecord, AttendanceSummary


class EvalServiceConsumer:
    """Consumer for eval-service to handle offer events."""
    
    def __init__(self):
        self.host = os.environ.get('RABBITMQ_HOST', 'localhost')  # Changed from 'rabbitmq' to 'localhost'
        self.port = int(os.environ.get('RABBITMQ_PORT', '5672'))
        self.exchange_name = 'medtrack.events'
        self.queue_name = 'eval.offers'
        
    def connect(self):
        """Connect to RabbitMQ and setup queue."""
        print(f"Connecting to RabbitMQ at {self.host}:{self.port}...")
        
        credentials = pika.PlainCredentials('admin', 'password')  # Changed from 'guest', 'guest'
        parameters = pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            credentials=credentials,
            heartbeat=600
        )
        
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        
        # Declare exchange
        channel.exchange_declare(
            exchange=self.exchange_name,
            exchange_type='topic',
            durable=True
        )
        
        # Declare queue (durable)
        channel.queue_declare(queue=self.queue_name, durable=True)
        
        # Bind to offer and affectation events
        channel.queue_bind(
            exchange=self.exchange_name,
            queue=self.queue_name,
            routing_key='core.offer.published'  # Published offers
        )
        channel.queue_bind(
            exchange=self.exchange_name,
            queue=self.queue_name,
            routing_key='core.affectation.created'  # Student assignments
        )
        
        print(f"✅ Connected! Listening for events on queue: {self.queue_name}")
        return connection, channel
    
    def handle_offer_published(self, event_data):
        """
        Handle offer.published event.
        
        When an offer is published, we can:
        - Create placeholder attendance records
        - Prepare for student assignment
        """
        offer_id = event_data.get('offer_id')
        title = event_data.get('title', 'Unknown')
        
        print(f"📢 Offer Published: {title} (ID: {offer_id})")
        print(f"   Ready to track attendance for this offer")
    
    def handle_affectation_created(self, event_data):
        """
        Handle affectation.created event.
        
        When a student is assigned to an offer:
        - Create AttendanceSummary for tracking
        - Prepare evaluation template
        """
        student_id = event_data.get('student_id')
        offer_id = event_data.get('offer_id')
        offer_title = event_data.get('offer_title', 'Unknown')
        affectation_id = event_data.get('affectation_id')
        
        print(f"✅ Student Assigned: {student_id}")
        print(f"   Offer: {offer_title}")
        print(f"   Creating attendance tracking...")
        
        # Create attendance summary
        try:
            AttendanceSummary.objects.create(
                student_id=student_id,
                offer_id=offer_id,
                total_days=0,
                present_days=0,
                presence_rate=0.0,
                validated=False
            )
            print(f"   ✅ Attendance summary created")
        except Exception as e:
            print(f"   ⚠️ Error creating summary: {e}")
    
    def process_message(self, ch, method, properties, body):
        """Process incoming RabbitMQ message."""
        try:
            # Parse event
            event = json.loads(body)
            event_type = event.get('event_type')
            data = event.get('data', {})
            
            print(f"\n📨 Received: {event_type}")
            
            # Route to appropriate handler
            if event_type == 'core.offer.published':
                self.handle_offer_published(data)
            elif event_type == 'core.affectation.created':
                self.handle_affectation_created(data)
            
            # Acknowledge message
            ch.basic_ack(delivery_tag=method.delivery_tag)
            print("✅ Message processed successfully")
            
        except Exception as e:
            print(f"❌ Error processing message: {e}")
            # Reject and requeue on error
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def start_consuming(self):
        """Start consuming messages."""
        while True:
            try:
                connection, channel = self.connect()
                
                # Set QoS
                channel.basic_qos(prefetch_count=1)
                
                # Start consuming
                channel.basic_consume(
                    queue=self.queue_name,
                    on_message_callback=self.process_message
                )
                
                print("\n🎧 Waiting for messages. Press CTRL+C to exit.\n")
                channel.start_consuming()
                
            except KeyboardInterrupt:
                print("\n👋 Shutting down consumer...")
                break
            except Exception as e:
                print(f"❌ Connection error: {e}")
                print("Reconnecting in 5 seconds...")
                sleep(5)


if __name__ == '__main__':
    consumer = EvalServiceConsumer()
    consumer.start_consuming()
