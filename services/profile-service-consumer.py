"""RabbitMQ consumer for PROFILE-SERVICE - Indexing and caching."""
import os
import json
import pika
from time import sleep


class ProfileServiceConsumer:
    """Consumer for profile-service to index and cache offer data."""
    
    def __init__(self):
        self.host = os.environ.get('RABBITMQ_HOST', 'localhost')  # Changed from 'rabbitmq' to 'localhost'
        self.port = int(os.environ.get('RABBITMQ_PORT', '5672'))
        self.exchange_name = 'medtrack.events'
        self.queue_name = 'profile.offers'
        
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
        
        # Bind to offer events for indexing
        channel.queue_bind(
            exchange=self.exchange_name,
            queue=self.queue_name,
            routing_key='core.offer.*'  # All offer events
        )
        
        print(f"✅ Connected! Listening for events on queue: {self.queue_name}")
        return connection, channel
    
    def index_offer(self, offer_data, action='index'):
        """Index offer data for search/caching."""
        offer_id = offer_data.get('offer_id')
        title = offer_data.get('title', 'Unknown')
        
        if action == 'index':
            print(f"📇 Indexing offer: {title} (ID: {offer_id})")
            # In real implementation:
            # - Add to Elasticsearch/search index
            # - Cache in Redis
            # - Update denormalized data
        elif action == 'update':
            print(f"📝 Updating index for offer: {offer_id}")
        elif action == 'delete':
            print(f"🗑️ Removing from index: {offer_id}")
    
    def handle_offer_created(self, data):
        """Index newly created offer."""
        self.index_offer(data, action='index')
    
    def handle_offer_published(self, data):
        """Update offer status to published in index."""
        offer_id = data.get('offer_id')
        print(f"📢 Marking offer as published in index: {offer_id}")
        self.index_offer(data, action='update')
    
    def handle_offer_updated(self, data):
        """Re-index updated offer."""
        self.index_offer(data, action='update')
    
    def handle_offer_closed(self, data):
        """Update offer status to closed in index."""
        offer_id = data.get('offer_id')
        print(f"🔒 Marking offer as closed in index: {offer_id}")
        self.index_offer(data, action='update')
    
    def handle_offer_deleted(self, data):
        """Remove offer from index."""
        self.index_offer(data, action='delete')
    
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
                'core.offer.updated': self.handle_offer_updated,
                'core.offer.closed': self.handle_offer_closed,
                'core.offer.deleted': self.handle_offer_deleted,
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
    consumer = ProfileServiceConsumer()
    consumer.start_consuming()
