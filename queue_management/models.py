from datetime import date
from django.conf import settings
from django.db import models
from django.utils import timezone

from patients.models import Patient


class QueueEntry(models.Model):
    WAITING = 'WAITING'
    CALLED = 'CALLED'
    IN_CONSULTATION = 'IN_CONSULTATION'
    COMPLETED = 'COMPLETED'
    NO_SHOW = 'NO_SHOW'
    CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (WAITING, 'Waiting'),
        (CALLED, 'Called'),
        (IN_CONSULTATION, 'In consultation'),
        (COMPLETED, 'Completed'),
        (NO_SHOW, 'No-show'),
        (CANCELLED, 'Cancelled'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='queue_entries')
    ticket_number = models.CharField(max_length=40, unique=True)
    queue_date = models.DateField(default=date.today)
    registered_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=WAITING)
    assigned_doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_queue_entries',
    )
    called_at = models.DateTimeField(null=True, blank=True)
    consultation_started_at = models.DateTimeField(null=True, blank=True)
    completion_time = models.DateTimeField(null=True, blank=True)
    no_show_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='queue_entries_created',
    )

    class Meta:
        ordering = ['registered_at']
        indexes = [
            models.Index(fields=['queue_date', 'status']),
            models.Index(fields=['status', 'registered_at']),
            models.Index(fields=['assigned_doctor', 'status']),
        ]

    def __str__(self):
        return f'{self.ticket_number} - {self.patient.full_name}'
