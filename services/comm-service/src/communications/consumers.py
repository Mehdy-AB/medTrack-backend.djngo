"""
WebSocket consumers for real-time communication
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time notifications and messages

    URL: ws://localhost/ws/notifications/{user_id}/

    Subscribes to user-specific channel to receive:
    - New messages
    - New notifications
    """

    async def connect(self):
        """Handle WebSocket connection"""
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_group_name = f'user_{self.user_id}'

        # Join user-specific channel
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"WebSocket connected for user {self.user_id}")

        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': f'Connected to notifications for user {self.user_id}'
        }))

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave user-specific channel
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"WebSocket disconnected for user {self.user_id}")

    async def receive(self, text_data):
        """
        Receive message from WebSocket (optional - for future use)
        Currently just echoes back
        """
        data = json.loads(text_data)
        logger.info(f"Received from user {self.user_id}: {data}")

        await self.send(text_data=json.dumps({
            'type': 'echo',
            'data': data
        }))

    async def message_created(self, event):
        """
        Handler for 'message_created' event
        Called when a new message is sent to this user
        """
        await self.send(text_data=json.dumps({
            'type': 'message_created',
            'data': event['data']
        }))

    async def notification_created(self, event):
        """
        Handler for 'notification_created' event
        Called when a new notification is created for this user
        """
        await self.send(text_data=json.dumps({
            'type': 'notification_created',
            'data': event['data']
        }))
