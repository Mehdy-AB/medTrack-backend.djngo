"""RabbitMQ consumer for COMM-SERVICE - Notifications."""
import os
import json
import pika
from time import sleep


class CommServiceConsumer:
    """Consumer for comm-service to send notifications."""
    
    def __init__(self):
        self.host = os.environ.get('RABBITMQ_HOST', 'localhost')  # Changed from 'rabbitmq' to 'localhost'
        self.port = int(os.environ.get('RABBITMQ_PORT', '5672'))
        self.exchange_name = 'medtrack.events'
        self.queue_name = 'comm.notifications'
        
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
        
        # Bind to all offer events and application events
        channel.queue_bind(
            exchange=self.exchange_name,
            queue=self.queue_name,
            routing_key='core.offer.*'  # All offer events
        )
        channel.queue_bind(
            exchange=self.exchange_name,
            queue=self.queue_name,
            routing_key='core.application.*'  # All application events
        )
        channel.queue_bind(
            exchange=self.exchange_name,
            queue=self.queue_name,
            routing_key='core.affectation.*'  # All affectation events
        )
        channel.queue_bind(
            exchange=self.exchange_name,
            queue=self.queue_name,
            routing_key='eval.attendance.*'  # All attendance events
        )
        channel.queue_bind(
            exchange=self.exchange_name,
            queue=self.queue_name,
            routing_key='eval.evaluation.*'  # All evaluation events
        )
        
        print(f"✅ Connected! Listening for events on queue: {self.queue_name}")
        return connection, channel
    
    def send_notification(self, notification_type, recipient, message):
        """Simulate sending notification (email/SMS/push)."""
        print(f"📧 Sending {notification_type} notification to {recipient}")
        print(f"   Message: {message}")
        # In real implementation: send email, SMS, or push notification
    
    def handle_offer_created(self, data):
        """Send notification when offer is created."""
        title = data.get('title', 'Unknown')
        created_by = data.get('created_by')
        
        if created_by:
            self.send_notification(
                'email',
                created_by,
                f"Your offer '{title}' has been created successfully!"
            )
    
    def handle_offer_published(self, data):
        """Send notification when offer is published."""
        title = data.get('title', 'Unknown')
        
        print(f"📢 Broadcasting: New offer published - {title}")
        # Notify all eligible students
        self.send_notification(
            'broadcast',
            'all_students',
            f"New internship opportunity: {title}"
        )
    
    def handle_offer_closed(self, data):
        """Send notification when offer is closed."""
        title = data.get('title', 'Unknown')
        offer_id = data.get('offer_id')
        
        print(f"🔒 Offer closed: {title}")
        # Notify applicants that offer is no longer accepting applications
    
    def handle_offer_deleted(self, data):
        """Send notification when offer is deleted."""
        offer_id = data.get('offer_id')
        print(f"🗑️ Offer deleted: {offer_id}")
    
    def handle_application_accepted(self, data):
        """Send notification when application is accepted."""
        student_id = data.get('student_id')
        offer_title = data.get('offer_title', 'an internship')
        
        self.send_notification(
            'email',
            student_id,
            f"Congratulations! Your application for '{offer_title}' has been accepted!"
        )
    
    def handle_application_rejected(self, data):
        """Send notification when application is rejected."""
        student_id = data.get('student_id')
        offer_title = data.get('offer_title', 'an internship')
        
        self.send_notification(
            'email',
            student_id,
            f"Your application for '{offer_title}' has been rejected."
        )
    
    def handle_application_submitted(self, data):
        """Send notification when application is submitted."""
        student_id = data.get('student_id')
        offer_title = data.get('offer_title', 'an internship')
        application_id = data.get('application_id')
        
        # Notify student (confirmation)
        self.send_notification(
            'email',
            student_id,
            f"Your application for '{offer_title}' has been submitted successfully!"
        )
        
        # Notify encadrant (new application received)
        print(f"📧 Notifying encadrant about new application {application_id}")
    
    def handle_application_updated(self, data):
        """Send notification when application is updated."""
        student_id = data.get('student_id')
        offer_title = data.get('offer_title', 'an internship')
        
        self.send_notification(
            'email',
            student_id,
            f"Your application for '{offer_title}' has been updated."
        )
    
    def handle_application_withdrawn(self, data):
        """Send notification when application is withdrawn."""
        student_id = data.get('student_id')
        offer_title = data.get('offer_title', 'an internship')
        
        self.send_notification(
            'email',
            student_id,
            f"You have withdrawn your application for '{offer_title}'."
        )
        
        # Notify encadrant
        print(f"📧 Notifying encadrant about withdrawn application")
    
    def handle_affectation_created(self, data):
        """Send notification when student is assigned to offer."""
        student_id = data.get('student_id')
        offer_title = data.get('offer_title', 'an internship')
        
        self.send_notification(
            'email',
            student_id,
            f"You have been assigned to: {offer_title}. Your internship starts soon!"
        )
        
        print(f"📧 Notifying encadrant about new student assignment")
    
    def handle_affectation_deleted(self, data):
        """Send notification when assignment is removed."""
        student_id = data.get('student_id')
        
        self.send_notification(
            'email',
            student_id,
            f"Your internship assignment has been removed."
        )
    
    def handle_attendance_justified(self, data):
        """Send notification when absence is justified."""
        student_id = data.get('student_id')
        date = data.get('date')
        justification = data.get('justification_reason', 'Provided')
        
        print(f"📧 Absence justified for {student_id} on {date}: {justification}")
    
    def handle_attendance_validated(self, data):
        """Send notification when attendance summary is validated."""
        student_id = data.get('student_id')
        validated = data.get('validated')
        presence_rate = data.get('presence_rate', 0)
        
        if validated:
            self.send_notification(
                'email',
                student_id,
                f"Your attendance has been validated! Presence rate: {presence_rate}%"
            )
        else:
            self.send_notification(
                'email',
                student_id,
                f"Your attendance validation has been revoked."
            )
    
    def handle_evaluation_submitted(self, data):
        """Send notification when evaluation is submitted."""
        student_id = data.get('student_id')
        grade = data.get('grade')
        
        self.send_notification(
            'email',
            student_id,
            f"Your evaluation has been submitted. Grade: {grade}/20"
        )
    
    def handle_evaluation_validated(self, data):
        """Send notification when supervisor validates evaluation."""
        student_id = data.get('student_id')
        validated = data.get('validated')
        grade = data.get('grade', 0)
        
        if validated:
            self.send_notification(
                'email',
                student_id,
                f"✅ Your evaluation has been validated! Final grade: {grade}/20"
            )
        else:
            self.send_notification(
                'email',
                student_id,
                f"Your evaluation validation has been revoked."
            )
    
    def process_message(self, ch, method, properties, body):
        """Process incoming RabbitMQ message."""
        try:
            # Parse event
            event = json.loads(body)
            event_type = event.get('event_type')
            data = event.get('data', {})
            
            print(f"\n📨 Received: {event_type}")
            
            # Route to appropriate handler
            handlers = {
                'core.offer.created': self.handle_offer_created,
                'core.offer.published': self.handle_offer_published,
                'core.offer.closed': self.handle_offer_closed,
                'core.offer.deleted': self.handle_offer_deleted,
                'core.application.submitted': self.handle_application_submitted,
                'core.application.updated': self.handle_application_updated,
                'core.application.withdrawn': self.handle_application_withdrawn,
                'core.application.accepted': self.handle_application_accepted,
                'core.application.rejected': self.handle_application_rejected,
                'core.affectation.created': self.handle_affectation_created,
                'core.affectation.deleted': self.handle_affectation_deleted,
                'eval.attendance.justified': self.handle_attendance_justified,
                'eval.attendance.validated': self.handle_attendance_validated,
                'eval.evaluation.submitted': self.handle_evaluation_submitted,
                'eval.evaluation.validated': self.handle_evaluation_validated,
            }
            
            handler = handlers.get(event_type)
            if handler:
                handler(data)
            
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
    consumer = CommServiceConsumer()
    consumer.start_consuming()
