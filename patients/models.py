from django.conf import settings
from django.db import models
from django.utils import timezone


class Patient(models.Model):
    patient_id = models.CharField(max_length=30, unique=True)
    full_name = models.CharField(max_length=150)
    date_of_birth = models.DateField(null=True, blank=True)
    sex = models.CharField(max_length=20, blank=True)
    phone_number = models.CharField(max_length=30, blank=True)
    registered_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='patients_created',
    )

    class Meta:
        indexes = [
            models.Index(fields=['full_name']),
            models.Index(fields=['patient_id']),
        ]

    def __str__(self):
        return f'{self.full_name} ({self.patient_id})'
