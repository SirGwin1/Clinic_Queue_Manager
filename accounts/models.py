from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ADMIN = 'ADMIN'
    RECEPTIONIST = 'RECEPTIONIST'
    DOCTOR = 'DOCTOR'

    ROLE_CHOICES = [
        (ADMIN, 'Administrator'),
        (RECEPTIONIST, 'Receptionist'),
        (DOCTOR, 'Doctor'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=RECEPTIONIST)

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.role})'
