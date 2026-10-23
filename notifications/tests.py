from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.test import TestCase

from accounts.models import User
from notifications.consumers import NotificationConsumer
from notifications.models import Notification


class NotificationTests(TestCase):
    def test_notifications_created_for_active_users(self):
        User.objects.create_user(username='admin', password='secret123', role=User.ADMIN)
        User.objects.create_user(username='doctor', password='secret123', role=User.DOCTOR)
        Notification.create_for_all('Queue update message')
        self.assertEqual(Notification.objects.count(), 2)

    async def test_authenticated_consumer_receives_queue_updates(self):
        user = await sync_to_async(User.objects.create_user)(
            username='websocket-user',
            password='secret123',
            role=User.DOCTOR,
        )
        communicator = WebsocketCommunicator(
            NotificationConsumer.as_asgi(),
            '/ws/notifications/',
        )
        communicator.scope['user'] = user

        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        self.assertEqual((await communicator.receive_json_from())['type'], 'connected')

        await get_channel_layer().group_send(
            'clinic_staff',
            {
                'type': 'queue.message',
                'message': 'A patient was called.',
                'notification_type': 'queue_update',
            },
        )
        notification = await communicator.receive_json_from(timeout=1)
        self.assertEqual(notification['type'], 'notification')
        self.assertEqual(notification['message'], 'A patient was called.')

        await communicator.disconnect()
