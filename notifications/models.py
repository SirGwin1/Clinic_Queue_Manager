from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.db import models


class Notification(models.Model):
    TYPE_CHOICES = [
        ('queue_update', 'Queue update'),
        ('alert', 'Alert'),
        ('system', 'System'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='queue_update')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_queue_entry = models.ForeignKey(
        'queue_management.QueueEntry',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
    )

    class Meta:
        ordering = ['-created_at']

    @classmethod
    def create_for_all(cls, message, notification_type='queue_update', related_queue_entry=None):
        from accounts.models import User

        for user in User.objects.filter(is_active=True):
            cls.objects.create(
                user=user,
                message=message,
                notification_type=notification_type,
                related_queue_entry=related_queue_entry,
            )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)('clinic_staff', {
            'type': 'queue.message',
            'message': message,
            'notification_type': notification_type,
        })

    def __str__(self):
        return self.message
