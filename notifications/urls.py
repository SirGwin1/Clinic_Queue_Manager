from django.urls import path
from .views import mark_notification_read, notification_center

urlpatterns = [
    path('', notification_center, name='notification_center'),
    path('mark-read/<int:pk>/', mark_notification_read, name='mark_notification_read'),
]
