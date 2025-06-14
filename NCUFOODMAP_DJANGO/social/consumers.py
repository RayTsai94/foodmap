import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import ChatRoom, ChatMessage

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'

        # 加入房間群組
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # 離開房間群組
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        user_id = self.scope["user"].id

        # 儲存訊息到資料庫
        chat_message = await self.save_message(user_id, message)
        
        # 廣播訊息到群組
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'user_id': user_id,
                'username': self.scope["user"].username,
                'timestamp': chat_message.timestamp.isoformat(),
                'avatar_url': chat_message.user.socialaccount_set.first().get_avatar_url() if chat_message.user.socialaccount_set.exists() else None
            }
        )

    async def chat_message(self, event):
        # 發送訊息到 WebSocket
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'user_id': event['user_id'],
            'username': event['username'],
            'timestamp': event['timestamp'],
            'avatar_url': event['avatar_url']
        }))

    @database_sync_to_async
    def save_message(self, user_id, message):
        room = ChatRoom.objects.get(id=self.room_id)
        user = self.scope["user"]
        chat_message = ChatMessage.objects.create(
            room=room,
            user=user,
            content=message,
            timestamp=timezone.now()
        )
        return chat_message 