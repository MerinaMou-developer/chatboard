from channels.generic.websocket import AsyncJsonWebsocketConsumer

class RoomConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.room = f"room:{self.scope['url_route']['kwargs']['room_id']}"
        await self.channel_layer.group_add(self.room, self.channel_name)
        await self.accept()

    async def receive_json(self, content):
        await self.channel_layer.group_send(self.room, {"type": "fanout", "payload": content})

    async def fanout(self, event):
        await self.send_json(event["payload"])

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room, self.channel_name)
