import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rooms.models import RoomMember

User = get_user_model()


class RoomConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        """Connect to WebSocket with JWT authentication."""
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f"room_{self.room_id}"
        
        # Get token from query parameters
        query_params = self.scope.get('query_string', b'').decode()
        token = None
        for param in query_params.split('&'):
            if param.startswith('token='):
                token = param.split('=')[1]
                break
        
        if not token:
            await self.close(code=4001)  # Unauthorized
            return
        
        # Authenticate user
        user = await self.authenticate_user(token)
        if not user:
            await self.close(code=4001)  # Unauthorized
            return
        
        # Check if user is member of the room
        is_member = await self.check_room_membership(user, self.room_id)
        if not is_member:
            await self.close(code=4003)  # Forbidden
            return
        
        self.user = user
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        
        # Send welcome message
        await self.send_json({
            'type': 'connection',
            'message': f'Connected to room {self.room_id}',
            'user_id': user.id,
            'user_email': user.email
        })

    async def disconnect(self, close_code):
        """Disconnect from WebSocket."""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive_json(self, content):
        """Handle incoming WebSocket messages."""
        message_type = content.get('type', 'message')
        
        if message_type == 'typing':
            # Broadcast typing indicator
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'user_id': self.user.id,
                    'user_email': self.user.email,
                    'is_typing': content.get('is_typing', False)
                }
            )
        elif message_type == 'ping':
            # Respond to ping with pong
            await self.send_json({'type': 'pong'})
        else:
            # Echo back the message (for testing)
            await self.send_json({
                'type': 'echo',
                'message': 'Message received',
                'original': content
            })

    async def fanout(self, event):
        """Handle messages from the room group."""
        await self.send_json(event["payload"])

    async def typing_indicator(self, event):
        """Handle typing indicators from other users."""
        await self.send_json({
            'type': 'typing',
            'user_id': event['user_id'],
            'user_email': event['user_email'],
            'is_typing': event['is_typing']
        })

    @database_sync_to_async
    def authenticate_user(self, token):
        """Authenticate user from JWT token."""
        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            return User.objects.get(id=user_id)
        except (InvalidToken, TokenError, User.DoesNotExist):
            return None

    @database_sync_to_async
    def check_room_membership(self, user, room_id):
        """Check if user is a member of the room."""
        return RoomMember.objects.filter(room_id=room_id, user=user).exists()
