from channels.generic.websocket import AsyncJsonWebsocketConsumer


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close()
            return

        self.room_group_name = 'clinic_staff'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        await self.send_json({'type': 'connected', 'message': 'WebSocket connected.'})

    async def queue_message(self, event):
        await self.send_json({
            'type': 'notification',
            'message': event['message'],
            'notification_type': event.get('notification_type', 'queue_update'),
        })

    async def disconnect(self, code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
